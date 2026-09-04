import json

from django.test import RequestFactory, SimpleTestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from common.auth import TokenAuth
from models_provider.api.provide import ProvideApi
from models_provider.constants.model_provider_constants import ModelProvideConstants
from models_provider.views.provide import Provide


EXPECTED_PROVIDER_IDS = [
    "model_azure_provider",
    "model_wenxin_provider",
    "model_ollama_provider",
    "model_openai_provider",
    "model_docker_ai_provider",
    "model_kimi_provider",
    "model_zhipu_provider",
    "model_xf_provider",
    "model_deepseek_provider",
    "model_gemini_provider",
    "model_volcanic_engine_provider",
    "model_tencent_provider",
    "model_tencent_cloud_provider",
    "model_aws_bedrock_provider",
    "model_local_provider",
    "model_xinference_provider",
    "model_vllm_provider",
    "aliyun_bai_lian_model_provider",
    "model_anthropic_provider",
    "model_siliconCloud_provider",
    "model_regolo_provider",
    "model_minimax_provider",
]


class ProvideApiTest(SimpleTestCase):
    def test_provider_list_response_matches_expected_shape(self):
        request = Request(RequestFactory().get("/admin/api/provider"))

        response = Provide().get(request)
        payload = json.loads(response.content)

        self.assertEqual(payload["code"], 200)
        self.assertIn("message", payload)
        self.assertIsInstance(payload["data"], list)
        self.assertEqual(len(payload["data"]), len(ModelProvideConstants.__members__))
        self.assertEqual([item["provider"] for item in payload["data"]], EXPECTED_PROVIDER_IDS)

        first_provider = payload["data"][0]
        self.assertEqual(set(first_provider.keys()), {"provider", "name", "icon"})
        self.assertEqual(first_provider["provider"], "model_azure_provider")
        self.assertEqual(first_provider["name"], "Azure OpenAI")
        self.assertTrue(first_provider["icon"].startswith("<svg"))

    def test_provider_response_schema_data_is_a_list(self):
        data_field = ProvideApi.get_response()().fields["data"]

        self.assertTrue(data_field.many)

    def test_provider_list_allows_unauthenticated_requests(self):
        request = APIRequestFactory().get("/admin/api/provider")

        response = Provide.as_view()(request)
        payload = json.loads(response.content)

        self.assertEqual(payload["code"], 200)
        self.assertIsInstance(payload["data"], list)

    def test_provider_list_ignores_stale_authorization_header(self):
        request = APIRequestFactory().get(
            "/admin/api/provider",
            HTTP_AUTHORIZATION="Bearer expired-token",
        )

        self.assertEqual(TokenAuth().authenticate(request), (None, None))
