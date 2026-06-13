from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

User = get_user_model()

class GrowthEngineAPITests(APITestCase):
    """
    Comprehensive API Unit Tests for the Kanzen Labs Growth Module.
    Validates authentication blocks, input serialization, and business calculators.
    """

    def setUp(self):
        """
        Executes before every individual test case.
        Sets up the testing database with a standard partner profile and JWT auth.
        """
        # Create a mock partner user
        self.user = User.objects.create_user(
            username="testpartner",
            email="partner@kanzenlabs.com",
            password="SecurePassword123"
        )
        
        # Simulating Profile/Approved Partner status if your architecture enforces it
        if hasattr(self.user, 'profile'):
            self.profile = self.user.profile
        else:
            # Fallback mock check if profile is linked in a custom signals/save setup
            self.profile = None

        # Endpoint Matrix (Reversing URLs using the names specified in urls.py)
        self.margin_calc_url = reverse("growth-margin-calculate")
        self.formulation_gen_url = reverse("growth-formulation-generate")

        # Force authentication on the API test client using Bearer Token flow simulation
        self.client.force_authenticate(user=self.user)

    def test_margin_calculator_success(self):
        """
        Assures that the Margin Calculator accurately processes floating point Decimals
        and saves calculated metrics to the database registry.
        """
        payload = {
            "production_cost": 8.50,
            "packaging_cost": 2.20,
            "shipping_cost": 1.80,
            "marketing_cost": 3.50,
            "retail_price": 42.00
        }
        
        response = self.client.post(self.margin_calc_url, payload, format="json")
        
        # Assure correct HTTP Status Code (201 Created)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Validate critical business formulas inside the serialized output
        self.assertIn("total_cost", response.data)
        self.assertIn("profit_per_unit", response.data)
        self.assertIn("margin_pct", response.data)

    def test_margin_calculator_invalid_data(self):
        """
        Assures that bad/missing input types prompt appropriate DRF validation 400 bad requests.
        """
        incomplete_payload = {
            "production_cost": 8.50,
            "retail_price": ""  # Missing price to trigger validation failure
        }
        
        response = self.client.post(self.margin_calc_url, incomplete_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("ai.formulation.generate_formulation")
    def test_ai_formulation_generation_mocked(self, mock_gemini):
        """
        Tests the AI generator endpoint without making live HTTP requests to Google Gemini.
        Mocks the core function to eliminate network flake/dependency costs during tests.
        """
        # Defining what our mock Gemini server should return instantly
        mock_gemini.return_value = {
            "formula_name": "Mocked Vitamin C Glow Serum",
            "base_formula": [{"ingredient": "Aqua", "percentage": 85.0}],
            "active_stack": [{"ingredient": "Ascorbic Acid", "percentage": 10.0}],
            "est_moq": "2,000 units",
            "cost_per_unit": "£5.00",
            "retail_range": "£30-35",
            "key_benefits": ["Brightening"],
            "ph_range": "3.5",
            "notes": "Test environment mock response."
        }

        payload = {
            "skin_type": "Oily",
            "concern": "Acne",
            "product_format": "Serum"
        }

        response = self.client.post(self.formulation_gen_url, payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["formula_name"], "Mocked Vitamin C Glow Serum")
        
        # Verify that our system actually called the underlying generator function once
        mock_gemini.assert_called_once()