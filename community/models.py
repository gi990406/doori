from django.db import models

# Create your models here.
class Notice(models.Model):
    """공지사항"""
    title = models.CharField(max_length=200, verbose_name="제목")
    content = models.TextField(verbose_name="내용")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "공지사항"
        verbose_name_plural = "공지사항"

class Notice_Image(models.Model):
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='notices/images/', verbose_name="이미지")

    def __str__(self):
        return f"{self.notice.title} - 이미지"
