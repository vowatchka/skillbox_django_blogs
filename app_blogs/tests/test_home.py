from django.test import TestCase
from django.urls import reverse


class HomePageTest(TestCase):
    tested_template = "all-blog-articles.html"
    tested_url_name = "home"

    def test_page(self):
        response = self.client.get(reverse(self.tested_url_name))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, self.tested_template)