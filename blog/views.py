# blog/views.py
from django.shortcuts import render, HttpResponse, HttpResponseRedirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required # permission_required adicionado
from django.core.paginator import Paginator
from django.db.models import Prefetch
from blog.models import PostMmrt, Comment, CarouselImage
from .forms import CommentForm, PostMmrtForm, CarouselImageForm
from django.contrib import messages # Importar o messages framework
from django.urls import reverse # Para redirecionamentos mais robustos
from django.contrib.auth.models import User, Group # User e Group adicionados para gerenciar usuários e grupos
from django.shortcuts import redirect # redirect adicionado para facilitar redirecionamentos
from googleapiclient.discovery import build # <--- Nova importação
from django.conf import settings # <--- Nova importação para acessar a chave de API
from googleapiclient.errors import HttpError # Importa para tratar erros específicos da API


# Define uma view para comment.
def addcomment(request, id):
    # Obtém o PostMmrt relacionado, ou retorna 404 se não existir
    post = get_object_or_404(PostMmrt, pk=id)
    
    # Define a URL de redirecionamento. Prefere o referer, mas tem um fallback seguro.
    # Em um projeto maior, você pode querer redirecionar para a URL de detalhes do post específico.
    url_redirect = request.META.get('HTTP_REFERER', reverse('home')) # Redireciona para a página anterior ou para a index

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            # Cria o comentário mas não salva ainda (commit=False)
            data = form.save(commit=False) 
            data.post = post  # Atribui o post ao comentário
            
            # Se o usuário estiver logado, usa o nome de usuário, senão usa o nome do formulário
            # Isso garante que o nome do usuário logado seja sempre o do sistema
            if request.user.is_authenticated:
                data.name = request.user.username
            else:
                data.name = form.cleaned_data['name'] # Fallback para o campo do formulário se não logado

            data.save() # Agora salva o comentário no banco
            messages.success(request, 'Seu comentário foi adicionado com sucesso e aguarda aprovação!') # Mensagem de sucesso
            return HttpResponseRedirect(url_redirect)
        else:
            # Se o formulário não for válido, adiciona mensagens de erro
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erro no campo '{field}': {error}")
            return HttpResponseRedirect(url_redirect) # Redireciona de volta com os erros
    
    # Se não for POST (acesso direto ou outro método), redireciona
    return HttpResponseRedirect(url_redirect)

# Define uma view baseada em função para a página inicial.
def index(request):
    # Prefetch os comentários aprovados para cada postagem
    # 'comments' é o related_name da relação entre PostMmrt e Comment (assumindo que seja esse)
    posts = PostMmrt.objects.order_by("-id").prefetch_related(
        Prefetch(
            'comments', # O related_name do seu ForeignKey ou ManyToManyField no modelo Comment para PostMmrt
            queryset=Comment.objects.filter(approved_comment=True),
            to_attr='approved_comments_list' # Nome do atributo que conterá os comentários aprovados
        )
    )

    posts_paginator = Paginator(posts, 5)
    page_num = request.GET.get('page')
    page_obj = posts_paginator.get_page(page_num)

    context = {
        'artigo': page_obj,
        'titulo': 'Igreja Mmrt',
        'Pagina_index': 'Home'
    }
    return render(request, 'index.html', context)

def videos(request):
    youtube_api_key = settings.YOUTUBE_API_KEY
    # IMPORTANTE: SUBSTITUA 'SEU_CANAL_ID_AQUI' pelo ID real do seu canal do YouTube.
    # Exemplo de um ID de canal: 'UC_XXXXXXXXXXXXXXXXXXXXXX'
    channel_id = 'UC2WOj4C0uHhKdlRW65Or69A'

    live_video_id = None
    live_video_title = None
    live_status_message = "Verificando transmissão ao vivo..." # Mensagem inicial

    youtube_recorded_videos = [] # Lista para armazenar informações dos vídeos gravados
    recorded_videos_message = "Carregando vídeos gravados..." # Mensagem inicial

    youtube_service = None # Objeto de serviço da API do YouTube

    # 1. Tenta inicializar o serviço da API do YouTube
    if not youtube_api_key:
        live_status_message = "Erro: A chave de API do YouTube não está configurada em settings.py."
        recorded_videos_message = "Erro: A chave de API do YouTube não está configurada em settings.py."
    else:
        try:
            youtube_service = build('youtube', 'v3', developerKey=youtube_api_key)
        except Exception as e:
            print(f"Erro ao inicializar o serviço YouTube API: {e}")
            live_status_message = "Erro ao conectar com a API do YouTube."
            recorded_videos_message = "Erro ao conectar com a API do YouTube."


    if youtube_service: # Se o serviço YouTube foi inicializado com sucesso, prossiga com as chamadas da API
        # 2. Lógica para buscar transmissão ao vivo do YouTube
        try:
            search_live_response = youtube_service.search().list(
                channelId=channel_id,
                eventType='live', # Busca apenas eventos ao vivo
                type='video',     # Busca por vídeos (que são as lives)
                part='id,snippet',
                maxResults=1      # Queremos apenas a live mais recente
            ).execute()

            if search_live_response.get('items'):
                # Encontrou uma transmissão ao vivo
                item = search_live_response['items'][0]
                if item['id']['kind'] == 'youtube#video':
                    live_video_id = item['id']['videoId']
                    live_video_title = item['snippet']['title']
                    live_status_message = "Transmissão Ao Vivo Agora:"
            else:
                live_status_message = "Nenhuma transmissão ao vivo no momento."

        except HttpError as e:
            print(f"Erro de HTTP ao buscar transmissão ao vivo do YouTube: {e}")
            live_status_message = f"Ocorreu um erro ao carregar a transmissão ao vivo. (Código: {e.resp.status})"
            # Para depuração, você pode querer logar mais detalhes de 'e'
        except Exception as e:
            print(f"Erro inesperado ao buscar transmissão ao vivo do YouTube: {e}")
            live_status_message = "Ocorreu um erro inesperado ao carregar a transmissão ao vivo."


        # 3. Lógica para buscar vídeos gravados do YouTube (uploads do canal)
        try:
            # Primeiro, precisamos do ID da playlist de uploads do canal
            channel_response = youtube_service.channels().list(
                id=channel_id,
                part='contentDetails'
            ).execute()

            uploads_playlist_id = None
            if channel_response.get('items'):
                uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

            if uploads_playlist_id:
                playlist_items_response = youtube_service.playlistItems().list(
                    playlistId=uploads_playlist_id,
                    part='snippet',
                    maxResults=9 # Número de vídeos gravados que você quer exibir (ex: os 9 mais recentes)
                ).execute()

                for item in playlist_items_response.get('items', []):
                    if item['snippet']['resourceId']['kind'] == 'youtube#video':
                        video_id_from_playlist = item['snippet']['resourceId']['videoId']

                        # Condição para FILTRAR: Se o vídeo é a live, NÃO o adiciona aos gravados
                        if live_video_id and video_id_from_playlist == live_video_id:
                            continue # Pula este vídeo se ele for o que está ao vivo

                        youtube_recorded_videos.append({
                            'id': video_id_from_playlist,
                            'title': item['snippet']['title'],
                            'thumbnail': item['snippet']['thumbnails']['medium']['url'] if 'medium' in item['snippet']['thumbnails'] else ''
                        })
                recorded_videos_message = "Nossos Últimos Vídeos Gravados"
            else:
                recorded_videos_message = "Não foi possível encontrar a playlist de uploads do canal."

        except HttpError as e:
            print(f"Erro de HTTP ao buscar vídeos gravados do YouTube: {e}")
            recorded_videos_message = f"Ocorreu um erro ao carregar os vídeos gravados. (Código: {e.resp.status})"
        except Exception as e:
            print(f"Erro inesperado ao buscar vídeos gravados do YouTube: {e}")
            recorded_videos_message = "Ocorreu um erro inesperado ao carregar os vídeos gravados."


    context = {
        'titulo': 'Nossos Vídeos', # Título geral da página
        'live_video_id': live_video_id,
        'live_video_title': live_video_title,
        'live_status_message': live_status_message,
        'youtube_recorded_videos': youtube_recorded_videos, # Agora é uma lista de dicionários
        'recorded_videos_message': recorded_videos_message,
    }
    return render(request, 'videos.html', context)

def home(request):
    # Lógica para obter imagens ativas do carrossel
    # Ordena por 'order' (ordem de exibição) e depois por '-created_at' (mais recente primeiro, em caso de mesma ordem)
    carousel_images = CarouselImage.objects.filter(is_active=True).order_by('order', '-created_at')

    context = {
        'titulo': 'Bem-vindo à MMRT!', # Seu título original
        'mensagem_boas_vindas': 'Explore nossos conteúdos e ministérios.', # Sua mensagem original
        'carousel_images': carousel_images, # Passa as imagens para o template home.html
    }
    return render(request, 'home.html', context)


@login_required
def perfil(request):
    # Verifica se o usuário tem a permissão para gerenciar posts (ou qualquer permissão de admin do blog)
    # Assumindo que a permissão 'blog.change_postmmrt' é a que define um "admin do blog"
    can_admin_blog = request.user.has_perm('blog.change_postmmrt')

    context = {
        'titulo': 'Meu Perfil',
        'can_admin_blog': can_admin_blog, # Passa a permissão como um booleano para o template
    }
    return render(request, 'perfil.html', context)


# Definir uma view baseada em função.
def quemsomos(request):
    return render(request, 'quemsomos.html', { 'titulo': 'Igreja Mmrt', 'Pagina_quesoueu': 'Igreja MMRT'})

# Definir uma view baseada em função.
def contato(request):
    return render(request, 'contato.html', { 'titulo': 'Dourados/Ms', 'Pagina_contato': 'Contato'})

# Definir uma view baseada em função.
def mundokids(request):
    return render(request, 'mundokids.html', { 'titulo': 'Ministério Infantil', 'Ministerio_Infantil': 'Ministério Infantil'})


# --- NOVAS VIEWS PARA O ADMIN DO BLOG ---

# View para o painel de administração do blog
@login_required
@permission_required('blog.change_postmmrt', raise_exception=True)
def blog_admin_dashboard(request):
    all_posts = PostMmrt.objects.all().order_by('-pub_date')
    all_comments = Comment.objects.all().order_by('-created_at')
    
    # MUITO IMPORTANTE: Garanta que esta linha exista e esteja correta
    pending_comments = Comment.objects.filter(approved_comment=False).count() 

    try:
        blog_admins_group = Group.objects.get(name='Blog Admins')
    except Group.DoesNotExist:
        blog_admins_group = None

    context = {
        'all_posts': all_posts,
        'all_comments': all_comments,
        'pending_comments': pending_comments, # <--- Esta variável PRECISA ser passada
        'titulo': 'Painel de Controle do Blog',
        'blog_admins_group': blog_admins_group,
    }
    return render(request, 'blog_admin_dashboard.html', context) # Verifique se o caminho do template está correto aqui

# View para criar um novo "Admin do Blog"
# Use 'auth.add_user' para que apenas superusuários (ou quem tiver essa permissão) possam criar novos usuários.
# Se você quiser que "Admins do Blog" criem outros "Admins do Blog", você precisará de uma permissão customizada.
@login_required
@permission_required('auth.add_user', raise_exception=True)
def create_blog_admin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email') # Email opcional

        if not username or not password:
            messages.error(request, 'Nome de usuário e senha são obrigatórios.')
            return render(request, 'create_blog_admin.html', {'titulo': 'Criar Admin do Blog'})

        try:
            # Cria o usuário padrão do Django
            user = User.objects.create_user(username=username, email=email, password=password)
            
            # Adiciona o usuário ao grupo 'Blog Admins'
            blog_admins_group = Group.objects.get(name='Blog Admins')
            user.groups.add(blog_admins_group)
            
            messages.success(request, f'Admin do Blog "{username}" criado e adicionado ao grupo com sucesso!')
            return redirect('blog_admin_dashboard') # Redireciona para o painel
        except Exception as e:
            messages.error(request, f'Erro ao criar admin do blog: {e}')

    return render(request, 'create_blog_admin.html', {'titulo': 'Criar Admin do Blog'})

@login_required
@permission_required('blog.add_postmmrt', raise_exception=True) # Exige permissão para adicionar posts
def create_post(request):
    if request.method == 'POST':
        form = PostMmrtForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user # Associa o post ao usuário logado
            post.save()
            messages.success(request, 'Post criado com sucesso!')
            return redirect('blog_admin_dashboard') # Ou para onde você quiser redirecionar
    else:
        form = PostMmrtForm()
    
    context = {
        'form': form,
        'titulo': 'Criar Novo Post',
    }
    return render(request, 'blog_admin/create_post.html', context) # Verifique o caminho do template

@login_required
@permission_required('blog.change_postmmrt', raise_exception=True)
def edit_post(request, post_id):
    post = get_object_or_404(PostMmrt, pk=post_id)

    if request.method == 'POST':
        form = PostMmrtForm(request.POST, instance=post) # Instancia o formulário com dados e o post existente
        if form.is_valid():
            form.save() # Salva as alterações
            messages.success(request, 'Post atualizado com sucesso!')
            return redirect('blog_admin_dashboard') # Redireciona para o painel
        else:
            # Se o formulário não for válido, adiciona mensagens de erro
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erro no campo '{field}': {error}")
    else: # Requisição GET (carregar a página de edição)
        form = PostMmrtForm(instance=post) # Popula o formulário com os dados existentes do post

    context = {
        'post': post,
        'titulo': f'Editar Post: {post.titulo_blog}', # Usa 'titulo_blog' corretamente aqui
        'form': form # Passa o formulário para o template
    }
    return render(request, 'edit_post.html', context)


@login_required
@permission_required('blog.delete_postmmrt', raise_exception=True) # Permissão para deletar posts
# @require_POST # Descomente esta linha para exigir que a requisição seja POST (mais seguro para deleção)
def delete_post(request, post_id):
    post = get_object_or_404(PostMmrt, pk=post_id)

    # Opcional: verifique se o usuário é o autor do post OU um superusuário
    # if post.author != request.user and not request.user.is_superuser:
    #     messages.error(request, "Você não tem permissão para deletar este post.")
    #     return redirect('blog_admin_dashboard')

    # Se você usar @require_POST, a verificação do método já é feita
    # Caso contrário, pode adicionar uma verificação manual:
    if request.method == 'POST': # Ou apenas if request.method == 'GET' se não usar @require_POST e quiser via GET
        post.delete()
        messages.success(request, 'Post deletado com sucesso!')
        return redirect('blog_admin_dashboard') # Redireciona para o painel após deletar

    # Se você quiser uma página de confirmação antes de deletar (recomendado):
    return render(request, 'delete_post_confirm.html', {'post': post})
    # Ou simplesmente redirecionar de volta se não for POST (se @require_POST não for usado)
    messages.error(request, 'Requisição inválida para deletar o post.')
    return redirect('blog_admin_dashboard')

@login_required
@permission_required('blog.change_comment', raise_exception=True)
def manage_comments(request):
    print("manage_comments view called!") # DEBUG
    if request.method == 'POST':
        print("Received POST request!") # DEBUG
        comment_id = request.POST.get('comment_id')
        action = request.POST.get('action')

        print(f"Comment ID: {comment_id}, Action: {action}") # DEBUG

        comment = get_object_or_404(Comment, id=comment_id)

        if action == 'approve':
            comment.approved_comment = True
            comment.save()
            messages.success(request, 'Comentário aprovado com sucesso!')
            print("Comment approved!") # DEBUG
        elif action == 'disapprove':
            comment.approved_comment = False
            comment.save()
            messages.info(request, 'Comentário desaprovado com sucesso!')
            print("Comment disapproved!") # DEBUG
        elif action == 'delete':
            comment.delete()
            messages.success(request, 'Comentário eliminado com sucesso!')
            print("Comment deleted!") # DEBUG
        else:
            messages.error(request, 'Ação inválida.')
            print("Invalid action received!") # DEBUG
        
        return redirect('manage_comments')

    else: # GET request
        print("Received GET request (displaying comments).") # DEBUG
        all_comments = Comment.objects.all().order_by('-created_at')
        pending_comments_count = Comment.objects.filter(approved_comment=False).count()

        context = {
            'all_comments': all_comments, # Use all_comments como na sua view
            'pending_comments': pending_comments_count,
            'titulo': 'Gerenciar Comentários',
        }
        return render(request, 'blog_admin_dashboard.html', context)


# --- Você pode REMOVER as views approve_comment e delete_comment SE manage_comments as consolidar ---
# Se ainda precisar de delete_comment para outros casos, mantenha-a, mas certifique-se
# que ela redireciona corretamente após a exclusão (por exemplo, para 'manage_comments').
# Exemplo de como delete_comment deveria ser se ainda existisse (e chamada separadamente):
# @login_required
# @permission_required('blog.delete_comment', raise_exception=True)
# def delete_comment(request, comment_id):
#     comment = get_object_or_404(Comment, pk=comment_id)
#     if request.method == 'POST':
#         comment.delete()
#         messages.success(request, 'Comentário eliminado com sucesso!')
#         return redirect('manage_comments') # Redireciona para a view de gestão
#     messages.error(request, 'Requisição inválida para eliminar o comentário.')
#     return redirect('manage_comments') # Ou para uma página de confirmação
# View para aprovar um comentário

@login_required
@permission_required('blog.change_comment', raise_exception=True) # Permissão para alterar comentários
def approve_comment(request):
    # Filtra comentários que AINDA NÃO FORAM APROVADOS
    # Use 'approved_comment=False'
    comments_pending_approval = Comment.objects.filter(approved_comment=False).order_by('-created_at')

    if request.method == 'POST':
        comment_id = request.POST.get('comment_id')
        action = request.POST.get('action') # 'approve' ou 'delete'

        comment = get_object_or_404(Comment, id=comment_id)

        if action == 'approve':
            comment.approve() # Chama o método approve do seu modelo Comment
            messages.success(request, 'Comentário aprovado com sucesso!')
        elif action == 'delete':
            comment.delete()
            messages.warning(request, 'Comentário excluído com sucesso!')

        return redirect('approve_comments') # Redireciona para a mesma página para atualizar a lista

    context = {
        'comments_list': comments_pending_approval, # Lista de comentários pendentes
        'titulo': 'Aprovar Comentários',
    }
    return render(request, 'blog_admin/approve_comments.html', context) # <--- Verifique o nome do seu template!l

@login_required
@permission_required('blog.view_carouselimage', raise_exception=True) # Permissão para ver
def carousel_image_list(request):
    """
    Lista todas as imagens do carrossel e permite adicionar novas.
    """
    images = CarouselImage.objects.all().order_by('order', '-created_at')
    form = CarouselImageForm()

    if request.method == 'POST':
        form = CarouselImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Imagem do carrossel adicionada com sucesso!')
            return redirect('carousel_image_list') # Redireciona para a mesma página para ver a lista atualizada
        else:
            messages.error(request, 'Erro ao adicionar imagem. Verifique os campos.')

    context = {
        'images': images,
        'form': form,
        'titulo': 'Gerir Imagens do Carrossel', # Alterado para 'Gerir Imagens do Carrossel'
    }
    return render(request, 'blog_admin/carousel_image_list.html', context)


@login_required
@permission_required('blog.change_carouselimage', raise_exception=True) # Permissão para alterar
def carousel_image_edit(request, pk):
    """
    Edita uma imagem existente do carrossel.
    """
    image = get_object_or_404(CarouselImage, pk=pk)
    if request.method == 'POST':
        form = CarouselImageForm(request.POST, request.FILES, instance=image)
        if form.is_valid():
            form.save()
            messages.success(request, 'Imagem do carrossel atualizada com sucesso!')
            return redirect('carousel_image_list')
        else:
            messages.error(request, 'Erro ao atualizar imagem. Verifique os campos.')
    else:
        form = CarouselImageForm(instance=image)

    context = {
        'form': form,
        'image': image,
        'titulo': f'Editar Imagem: {image.title or image.id}',
    }
    return render(request, 'blog_admin/carousel_image_edit.html', context)


@login_required
@permission_required('blog.delete_carouselimage', raise_exception=True) # Permissão para apagar
def carousel_image_delete(request, pk):
    """
    Apaga uma imagem do carrossel.
    """
    image = get_object_or_404(CarouselImage, pk=pk)
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Imagem do carrossel eliminada com sucesso!') # Alterado para 'eliminada'
        return redirect('carousel_image_list')
    
    context = {
        'image': image,
        'titulo': f'Confirmar Eliminação: {image.title or image.id}', # Alterado para 'Eliminação'
    }
    return render(request, 'blog_admin/carousel_image_confirm_delete.html', context)