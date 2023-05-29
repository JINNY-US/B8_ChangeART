from django.urls import reverse
from rest_framework.test import APITestCase
from faker import Faker

from users.models import User
from .models import Article
from .serializers import ArticleDetailSerializer

# 임시 이미지 생성용 패키지
from django.test.client import MULTIPART_CONTENT, encode_multipart, BOUNDARY
from PIL import Image
import tempfile


# 임시 이미지 생성
def get_temporary_image(temp_file):
    size = (200, 200)
    color = (255, 0, 0, 0)
    image = Image.new("RGBA", size, color)
    image.save(temp_file, "png")
    return temp_file


class ArticleViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("article@test.com", "테스트", "1234")
        cls.login_data = {"email": "article@test.com", "password": "1234"}
        cls.article_data = {"title": "게시글 제목", "content": "게시글 내용"}
        cls.faker = Faker()
        cls.articles = []
        for i in range(5):
            cls.user = User.objects.create_user(
                f"{i}@test.com", cls.faker.word(), cls.faker.word()
            )
            cls.articles.append(
                Article.objects.create(
                    title=cls.faker.sentence(), content=cls.faker.text(), user=cls.user
                )
            )

    def setUp(self):
        self.access_token = self.client.post(
            reverse("login_view"), self.login_data
        ).data["access"]

    def test_create_fail_article(self):
        url = reverse("article_create_view")
        response = self.client.post(url, self.article_data)
        self.assertEqual(response.status_code, 401)

    def test_create_success_article(self):
        response = self.client.post(
            path=reverse("article_create_view"),
            data=self.article_data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.data["message"], "게시글을 등록했습니다.")

    def test_create_article_with_image(self):
        # 임시 이미지 파일 생성
        temp_file = tempfile.NamedTemporaryFile()
        temp_file.name = "image.png"
        image_file = get_temporary_image(temp_file)
        image_file.seek(0)
        self.article_data["image"] = image_file
        # 전송
        response = self.client.post(
            path=reverse("article_create_view"),
            data=encode_multipart(data=self.article_data, boundary=BOUNDARY),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.data["message"], "게시글을 등록했습니다.")

    def test_get_article(self):
        for article in self.articles:
            url = article.get_absolute_url()
            response = self.client.get(url)
            serializer = ArticleDetailSerializer(article).data
            for key, value in serializer.items():
                self.assertEqual(response.data[key], value)


class ArticleLikeViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("article@test.com", "테스트", "1234")
        cls.login_data = {"email": "article@test.com", "password": "1234"}
        cls.faker = Faker()
        cls.articles = []
        for i in range(5):
            cls.user = User.objects.create_user(
                f"{i}@test.com", cls.faker.word(), cls.faker.word()
            )
            cls.articles.append(
                Article.objects.create(
                    title=cls.faker.sentence(), content=cls.faker.text(), user=cls.user
                )
            )

    def setUp(self):
        self.access_token = self.client.post(
            reverse("login_view"), self.login_data
        ).data["access"]

    def test_article_like(self):
        for article in self.articles:
            url = article.get_absolute_url()
            for _ in range(2):
                response = self.client.post(
                    path=reverse("article_like_view", args=[url.split("/")[1]]),
                    HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
                )
                self.assertEqual(response.status_code, 200)


class CommentViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("article@test.com", "테스트", "1234")
        cls.login_data = {"email": "article@test.com", "password": "1234"}
        cls.faker = Faker()
        cls.article = Article.objects.create(
            title=cls.faker.sentence(), content=cls.faker.text(), user=cls.user
        )
        cls.article_id = cls.article.get_absolute_url().split("/")[1]
        cls.data = {"content": "댓글 작성 테스트"}
        cls.put_data = {"content": "댓글 수정 테스트"}

    def setUp(self):
        self.access_token = self.client.post(
            reverse("login_view"), self.login_data
        ).data["access"]
        self.before_comment = self.client.post(
            path=reverse("comment_create_view", args=[self.article_id]),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            data=self.data,
        )
        self.comment_id = self.before_comment.data["id"]

    def test_post_comment(self):
        response = self.client.post(
            path=reverse("comment_create_view", args=[self.article_id]),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            data=self.data,
        )
        self.assertEqual(response.data["content"], "댓글 작성 테스트")

    def test_put_comment(self):
        response = self.client.put(
            path=reverse("comment_view", args=[self.comment_id]),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            data=self.put_data,
        )
        self.assertEqual(response.data["content"], "댓글 수정 테스트")

    def test_delete_comment(self):
        response = self.client.delete(
            path=reverse("comment_view", args=[self.comment_id]),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            data=self.put_data,
        )
        self.assertEqual(response.data["message"], "댓글 삭제")
