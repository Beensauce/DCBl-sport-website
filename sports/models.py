from django.db import models
import random
from PIL import Image
from django.conf import settings
# Create your models here.

class Team(models.Model):
    SPORT_CHOICES = [
        ('VB', 'Volleyball'),
        ('FB', 'Football'),
        ('BB', 'Basketball'),
        ('TE', 'Tennis'),
        ('BD', 'Badminton'),
        ('TR', 'Track & Field'),
        ('SW', 'Swimming'),
    ]
    
    LEVEL_CHOICES = [
        ('BV', 'Boys Varsity'),
        ('GV', 'Girls Varsity'),
        ('JV', 'Junior Varsity'),
        ('U14B', 'Boys U14s A'),
        ('U14G', 'Girls U14s'),
        ('14B', 'U14s A'),
        ('y7', 'Year 7'),
    ]

    SEASON_CHOICES = [
        ('1', 'Season 1'),
        ('2', 'Season 2'),
        ('3', 'Season 3'),
        ('4', 'Season 4'),
    ]
    
    season = models.CharField(max_length=10, choices=SEASON_CHOICES)
    year = models.IntegerField(default=2025, blank=True, help_text="e.g., 9th, 10th, 11th, 12th")
    name = models.CharField(max_length=100, help_text="e.g., Boys Volleyball, Girls Soccer")
    sport = models.CharField(max_length=5, choices=SPORT_CHOICES)
    level = models.CharField(max_length=5, choices=LEVEL_CHOICES)
    description = models.TextField(blank=True, help_text="Brief team description or motto")
    photo = models.ImageField(upload_to='teams/photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    honors = models.CharField(max_length=100, help_text="Honors")
    instagram = models.URLField(blank=True, null=True)
    
    def get_captain(self):
        return self.players.filter(is_captain=True).first()
    
    def get_coach(self):
        return self.coaches.filter(is_student_coach=False)
    
    def get_student_coach(self):
         return self.coaches.filter(is_student_coach=True)

    class Meta:
        ordering = ['sport', 'level', 'name']
        unique_together = ['name', 'sport', 'level']

    def __str__(self):
        return f"{self.get_level_display()} {self.get_sport_display()}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.photo:
            img = Image.open(self.photo.path)

            if img.height > 1920 or img.width > 1080:
                output_size = (1920, 1080)
                img.thumbnail(output_size) # Maintain aspect ratio
                img.save(self.photo.path)


class Coach(models.Model):
    is_student_coach = models.BooleanField(default=False)
    name = models.CharField(max_length=300)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="coaches")
    photo = models.ImageField(upload_to='legends/', blank=True, null=True)
    year = models.CharField(max_length=10, blank=True, help_text="e.g., 9th, 10th, 11th, 12th")

    DEFAULT_PICS = [
        'amongus/Orange.png',
        'amongus/Yellow.png',
        'amongus/White.png',
        'amongus/Red.png',
        'amongus/Purple.png',
    ]

    def __str__(self):
        return f"{self.name} - {self.team}"
    
    def profile_pic_url(self):
        if self.photo:
            return self.photo.url
        else:
            return settings.MEDIA_URL + random.choice(self.DEFAULT_PICS)
        
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.photo:
            img = Image.open(self.photo.path)

            if img.height > 150 or img.width > 350:
                output_size = (500, 500)
                img.thumbnail(output_size) # Maintain aspect ratio
                img.save(self.photo.path)


class Player(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    position = models.CharField(max_length=50, blank=True)
    year = models.CharField(max_length=10, blank=True, help_text="e.g., 9th, 10th, 11th, 12th")
    photo = models.ImageField(upload_to='players/photos/', blank=True, null=True, default='')
    is_captain = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    shirt_number = models.IntegerField(blank=True, null=True)
    quote = models.CharField(max_length=500, blank=True, null=True)
    
    DEFAULT_PICS = [
        'amongus/Orange.png',
        'amongus/Yellow.png',
        'amongus/White.png',
        'amongus/Red.png',
        'amongus/Purple.png',
    ]

    class Meta:
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def profile_pic_url(self):
        if self.photo:
            return self.photo.url
        else:
            return settings.MEDIA_URL + random.choice(self.DEFAULT_PICS)
        
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.photo:
            img = Image.open(self.photo.path)

            if img.height > 150 or img.width > 350:
                output_size = (500, 500)
                img.thumbnail(output_size) # Maintain aspect ratio
                img.save(self.photo.path)
    

class Opposition(models.Model):
    name = models.CharField(max_length=50)
    opp_logo = models.ImageField(upload_to='teams/opposition/photos/', blank=True, null=True)

    def __str__(self):
        return f"{self.name}"


class Game(models.Model):
    dcb_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='dcb_team')
    opposition = models.ForeignKey(Opposition, on_delete=models.Case, related_name='opposition_team')
    dcb_score = models.IntegerField()
    opp_score = models.IntegerField()
    date = models.DateField()
    time = models.TimeField()  # This is what you want for manual time
    location = models.CharField(max_length=200)
    is_finished = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.dcb_team} vs {self.opposition} - {self.date} {self.time}"
    
    @property
    def datetime_combined(self):
        from datetime import datetime
        return datetime.combine(self.date, self.time)


class Event(models.Model):
    event_name = models.CharField(max_length=50)
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='events/')

    def __str__(self):
        return self.event_name
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.photo:
            img = Image.open(self.photo.path)

            if img.height > 1920 or img.width > 1080:
                output_size = (1920, 1080)
                img.thumbnail(output_size) # Maintain aspect ratio
                img.save(self.photo.path)


class Legend(models.Model):
    name = models.CharField(max_length=300)
    teams = models.CharField(max_length=200)
    image = models.ImageField(upload_to='legends/', blank=True, null=True)
    description = models.TextField()

    DEFAULT_PICS = [
        'amongus/Orange.png',
        'amongus/Yellow.png',
        'amongus/White.png',
        'amongus/Red.png',
        'amongus/Purple.png',
    ]
    
    def __str__(self):
        return self.name
    
    def profile_pic_url(self):
        if self.image:
            return self.image.url
        else:
            return settings.MEDIA_URL + random.choice(self.DEFAULT_PICS)
        