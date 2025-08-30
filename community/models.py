from django.db import models
from django.conf import settings

# Create your models here.
class Notice(models.Model):
    """공지사항"""
    title = models.CharField(max_length=200, verbose_name="제목")
    content = models.TextField(verbose_name="내용")
    hits = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "공지사항"
        verbose_name_plural = "공지사항"

class Notice_Image(models.Model):
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='notices/images/', verbose_name="이미지", help_text="이미지는 게시글 상단에 보여집니다.")

    def __str__(self):
        return f"{self.notice.title} - 이미지"

class QuoteInquiry(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "접수"
        ANSWERED = "ANSWERED", "답변완료"
        CLOSED = "CLOSED", "종결"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quote_inquiries")
    title = models.CharField(max_length=200)
    content = models.TextField()
    attachment = models.FileField(upload_to="quote_attachments/", blank=True, null=True)
    is_private = models.BooleanField(default=False, help_text="비공개 설정 시 본인과 관리자만 열람")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "견적 문의"
        verbose_name_plural = "견적 문의"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title}"

class QuoteComment(models.Model):
    inquiry = models.ForeignKey(QuoteInquiry, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quote_comments")
    content = models.TextField()
    is_from_admin = models.BooleanField(default=False)  # staff 여부 캐싱용(표시/스타일)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
