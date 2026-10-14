from .models import DigestRequest, DigestResult


def build_digest(request: DigestRequest) -> DigestResult:
    """Build one buyer's digest without exposing another buyer's order state."""
    published = [asset for asset in request.seller_assets if asset.status == "published"]
    updates = [update for update in request.buyer_updates if update.buyer_email == request.audience_email]
    handoffs = [
        handoff
        for handoff in request.order_handoffs
        if handoff.ready and handoff.buyer_email == request.audience_email
    ]

    lines = [
        f"New from {asset.seller_name}: {asset.title} ({asset.storefront_url})"
        for asset in published
    ]
    lines.extend(f"{update.topic}: {update.detail}" for update in updates)
    lines.extend(
        f"Order {handoff.order_number} with {handoff.seller_name}: {handoff.next_step}"
        for handoff in handoffs
    )
    if not lines:
        lines.append("No storefront or order updates for this buyer this week.")

    return DigestResult(
        recipient=request.audience_email,
        subject=f"Marketplace dispatch - {request.week_label}",
        lines=lines,
    )
