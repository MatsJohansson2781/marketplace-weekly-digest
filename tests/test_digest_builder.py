from marketplace_digest.digest_builder import build_digest
from marketplace_digest.models import DigestRequest


def test_digest_keeps_order_handoffs_with_their_buyer() -> None:
    request = DigestRequest.model_validate(
        {
            "audience_email": "mina@example.com",
            "week_label": "September 7",
            "seller_assets": [
                {
                    "seller_name": "Field & Kiln",
                    "title": "Breakfast bowl",
                    "storefront_url": "https://shop.example.com/bowl",
                    "status": "published",
                },
                {
                    "seller_name": "Field & Kiln",
                    "title": "Winter glaze preview",
                    "storefront_url": "https://shop.example.com/glaze",
                    "status": "draft",
                },
            ],
            "buyer_updates": [],
            "order_handoffs": [
                {
                    "order_number": "A-1042",
                    "buyer_email": "mina@example.com",
                    "seller_name": "Field & Kiln",
                    "next_step": "Choose a pickup window.",
                    "ready": True,
                },
                {
                    "order_number": "B-991",
                    "buyer_email": "other@example.com",
                    "seller_name": "Paper Harbor",
                    "next_step": "Confirm the delivery address.",
                    "ready": True,
                },
            ],
        }
    )

    result = build_digest(request)

    assert result.lines == [
        "New from Field & Kiln: Breakfast bowl (https://shop.example.com/bowl)",
        "Order A-1042 with Field & Kiln: Choose a pickup window.",
    ]
