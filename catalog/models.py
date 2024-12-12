from django.db import models
from django.urls import reverse #Used to generate URLs by reversing the URL patterns
import uuid # Required for unique book instances
from django.contrib.auth.models import User
from datetime import date
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings



from django.contrib.auth.models import AbstractUser, BaseUserManager

class AdvUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class AdvUser(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    email = models.EmailField(unique=True)
    is_activated = models.BooleanField(default=True, db_index=True, verbose_name='Прошел активацию?')
    last_name = models.CharField(max_length=100, blank=True, verbose_name='Фамилия')
    first_name = models.CharField(max_length=100, blank=True, verbose_name='Имя')
    patronymic = models.CharField(max_length=100, blank=True, verbose_name='Отчество')
    consent = models.BooleanField(default=False, verbose_name='Согласие на обработку персональных данных')

    objects = AdvUserManager()  # Указываем наш кастомный менеджер

    class Meta(AbstractUser.Meta):
        pass

    # Уникальные имена для обратных связей
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='advuser_set',  # Уникальное имя для связи с группами
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='advuser_set',  # Уникальное имя для связи с разрешениями
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    class Meta(AbstractUser.Meta):
        pass

class Genre(models.Model): #Модель жанра
    """
    Model representing a book genre (e.g. Science Fiction, Non Fiction).
    """
    name = models.CharField(max_length=200,
                            help_text="Enter a book genre (e.g. Science Fiction, French Poetry etc.)", verbose_name=("Имя"))

    def __str__(self):
        """
        String for representing the Model object (in Admin site etc.)
        """
        return self.name

class Book(models.Model):  #Модель кинги
    """
    Model representing a book (but not a specific copy of a book).
    """
    title = models.CharField(max_length=200, verbose_name=("Название"))
    author = models.ForeignKey('Author', on_delete=models.SET_NULL, null=True, verbose_name=("Автор"))
    # Foreign Key used because book can only have one author, but authors can have multiple books
    # Author as a string rather than object because it hasn't been declared yet in the file.
    summary = models.TextField(max_length=1000, help_text="Enter a brief description of the book", verbose_name=("Описание"))
    isbn = models.CharField('ISBN', max_length=13,
                            help_text='13 Character <a href="https://www.isbn-international.org/content/what-isbn">ISBN number</a>')
    genre = models.ManyToManyField(Genre, help_text="Select a genre for this book", verbose_name=("Жанр"))

    # ManyToManyField used because genre can contain many books. Books can cover many genres.
    # Genre class has already been defined so we can specify the object above.


    def __str__(self):
        """
        String for representing the Model object.
        """
        return self.title

    def get_absolute_url(self):
        """
        Returns the url to access a particular book instance.
        """
        return reverse('book-detail', args=[str(self.id)])

    def display_genre(self):
        """
        Creates a string for the Genre. This is required to display genre in Admin.
        """
        return ', '.join([genre.name for genre in self.genre.all()[:3]])
    display_genre.short_description = 'Genre'


class BookInstance(models.Model):  #Модель BookInstance
    """
    Model representing a specific copy of a book (i.e. that can be borrowed from the library).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                          help_text="Unique ID for this particular book across whole library")
    book = models.ForeignKey('Book', on_delete=models.SET_NULL, null=True, verbose_name=("Книга"))
    imprint = models.CharField(max_length=200, verbose_name=("Год выпуска"))
    due_back = models.DateField(null=True, blank=True, verbose_name=("Дата возврата"))
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=("Заёмщик"))

    LOAN_STATUS = (
        ('m', 'На тех. обслуживании'),
        ('o', 'Доступна'),
        ('a', 'Взята'),
        ('r', 'Забронирована'),
    )

    status = models.CharField(max_length=1, choices=LOAN_STATUS, blank=True, default='m',
                              help_text='Book availability', verbose_name=("Состояние"))

    class Meta:
        ordering = ["due_back"]

    def __str__(self):
        """
        String for representing the Model object
        """
        return '%s (%s)' % (self.id, self.book.title)

    @property
    def is_overdue(self):
        if self.due_back and date.today() > self.due_back:
            return True
        return False

class Author(models.Model):  #Модель автора
    """
    Model representing an author.
    """
    first_name = models.CharField(max_length=100, verbose_name=("Имя автора"))
    last_name = models.CharField(max_length=100, verbose_name=("Фамилия автора"))
    date_of_birth = models.DateField(null=True, blank=True, verbose_name=("Дата рождения"))
    date_of_death = models.DateField('Дата смерти', null=True, blank=True)

    def get_absolute_url(self):
        """
        Returns the url to access a particular author instance.
        """
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        """
        String for representing the Model object.
        """
        return '%s, %s' % (self.last_name, self.first_name)

    def display_books(self):
        """
        Создает строку для отображения названий книг.
        Это необходимо для отображения книг в админке.
        """
        return ', '.join([book.title for book in Book.objects.filter(author=self)[:3]])
    display_books.short_description = 'Books'


