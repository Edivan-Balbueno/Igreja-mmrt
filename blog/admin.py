from django.contrib import admin
from .models import PostMmrt, Comment, CarouselImage
from django_summernote.admin import SummernoteModelAdmin

# Register your models here.
class PostMmrtAdmin(SummernoteModelAdmin):
    list_filter = ('titulo_blog',)
    summernote_fields = ('conteudo_artigo',)

class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'approved_comment']

admin.site.register(PostMmrt, PostMmrtAdmin)
admin.site.register(Comment, CommentAdmin)

@admin.register(CarouselImage)
class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title',)
    ordering = ('order',) # Garante que a ordenação padrão no admin é pelo campo 'order'
    fieldsets = (
        (None, {
            'fields': ('title', 'image', 'is_active', 'order')
        }),
    )
