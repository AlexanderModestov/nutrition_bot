import uuid
import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from yookassa import Configuration, Payment
from yookassa.domain.common import ConfirmationType
from bot.config import Config

logger = logging.getLogger(__name__)

class YooKassaService:
    """
    YooKassa payment service following the ElevenLabs service pattern.
    Handles payment creation, status checking, and webhook verification.
    """

    def __init__(self, shop_id: Optional[str] = None, secret_key: Optional[str] = None):
        """
        Initialize YooKassa service

        Args:
            shop_id: YooKassa shop ID (defaults to Config.YOOKASSA_SHOP_ID)
            secret_key: YooKassa secret key (defaults to Config.YOOKASSA_SECRET_KEY)
        """
        self.shop_id = shop_id or Config.YOOKASSA_SHOP_ID
        self.secret_key = secret_key or Config.YOOKASSA_SECRET_KEY

        if not self.shop_id or not self.secret_key:
            raise ValueError("YooKassa credentials are required. Set YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY")

        # Configure YooKassa SDK
        Configuration.account_id = self.shop_id
        Configuration.secret_key = self.secret_key

        logger.info("YooKassa service initialized")

    def generate_idempotence_key(self) -> str:
        """Generate unique idempotence key for payment requests"""
        return str(uuid.uuid4())

    def create_payment(
        self,
        amount: Decimal,
        currency: str = "RUB",
        description: str = "",
        return_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        idempotence_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new payment

        Args:
            amount: Payment amount
            currency: Currency code (default: RUB)
            description: Payment description
            return_url: URL to redirect after payment
            metadata: Additional metadata
            idempotence_key: Idempotence key (auto-generated if not provided)

        Returns:
            Dict with payment data:
                - payment_id: YooKassa payment ID
                - status: Payment status
                - confirmation_url: URL for user to complete payment
                - amount: Payment amount
                - currency: Currency
                - metadata: Payment metadata

        Raises:
            Exception: If payment creation fails
        """
        try:
            if idempotence_key is None:
                idempotence_key = self.generate_idempotence_key()

            return_url = return_url or Config.YOOKASSA_RETURN_URL

            # Create payment request
            payment_data = {
                "amount": {
                    "value": str(amount),
                    "currency": currency
                },
                "confirmation": {
                    "type": ConfirmationType.REDIRECT,
                    "return_url": return_url
                },
                "capture": True,  # Auto-capture payment
                "description": description
            }

            if metadata:
                payment_data["metadata"] = metadata

            logger.info(f"Creating YooKassa payment: amount={amount} {currency}, description='{description}'")

            # Create payment via YooKassa SDK
            payment = Payment.create(payment_data, idempotence_key)

            result = {
                "payment_id": payment.id,
                "status": payment.status,
                "confirmation_url": payment.confirmation.confirmation_url if payment.confirmation else None,
                "confirmation_type": payment.confirmation.type if payment.confirmation else None,
                "amount": Decimal(payment.amount.value),
                "currency": payment.amount.currency,
                "created_at": payment.created_at,
                "metadata": payment.metadata,
                "idempotence_key": idempotence_key
            }

            logger.info(f"Payment created successfully: payment_id={payment.id}, status={payment.status}")
            return result

        except Exception as e:
            logger.error(f"Failed to create payment: {e}")
            raise Exception(f"Payment creation failed: {str(e)}")

    def create_embedded_payment(
        self,
        amount: Decimal,
        currency: str = "RUB",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        idempotence_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an embedded payment for WebApp (returns confirmation_token instead of URL)

        Args:
            amount: Payment amount
            currency: Currency code (default: RUB)
            description: Payment description
            metadata: Additional metadata
            idempotence_key: Idempotence key (auto-generated if not provided)

        Returns:
            Dict with payment data:
                - payment_id: YooKassa payment ID
                - status: Payment status
                - confirmation_token: Token for embedded widget
                - amount: Payment amount
                - currency: Currency
                - metadata: Payment metadata

        Raises:
            Exception: If payment creation fails
        """
        try:
            if idempotence_key is None:
                idempotence_key = self.generate_idempotence_key()

            # Create payment request with EMBEDDED confirmation type
            payment_data = {
                "amount": {
                    "value": str(amount),
                    "currency": currency
                },
                "confirmation": {
                    "type": "embedded"
                },
                "capture": True,  # Auto-capture payment
                "description": description
            }

            if metadata:
                payment_data["metadata"] = metadata

            logger.info(f"Creating embedded YooKassa payment: amount={amount} {currency}, description='{description}'")

            # Create payment via YooKassa SDK
            payment = Payment.create(payment_data, idempotence_key)

            result = {
                "payment_id": payment.id,
                "status": payment.status,
                "confirmation_token": payment.confirmation.confirmation_token if payment.confirmation else None,
                "confirmation_type": payment.confirmation.type if payment.confirmation else None,
                "amount": Decimal(payment.amount.value),
                "currency": payment.amount.currency,
                "created_at": payment.created_at,
                "metadata": payment.metadata,
                "idempotence_key": idempotence_key
            }

            logger.info(f"Embedded payment created successfully: payment_id={payment.id}, status={payment.status}")
            return result

        except Exception as e:
            logger.error(f"Failed to create embedded payment: {e}")
            raise Exception(f"Embedded payment creation failed: {str(e)}")

    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Get payment status from YooKassa

        Args:
            payment_id: YooKassa payment ID

        Returns:
            Dict with payment status data:
                - payment_id: YooKassa payment ID
                - status: Payment status
                - paid: Whether payment is completed
                - amount: Payment amount
                - currency: Currency
                - payment_method: Payment method type
                - paid_at: Payment completion timestamp
                - metadata: Payment metadata

        Raises:
            Exception: If status check fails
        """
        try:
            logger.info(f"Checking payment status: payment_id={payment_id}")

            payment = Payment.find_one(payment_id)

            result = {
                "payment_id": payment.id,
                "status": payment.status,
                "paid": payment.paid,
                "amount": Decimal(payment.amount.value),
                "currency": payment.amount.currency,
                "payment_method": payment.payment_method.type if payment.payment_method else None,
                "paid_at": payment.captured_at if payment.paid else None,
                "metadata": payment.metadata,
                "created_at": payment.created_at
            }

            logger.info(f"Payment status retrieved: payment_id={payment_id}, status={payment.status}, paid={payment.paid}")
            return result

        except Exception as e:
            logger.error(f"Failed to get payment status: {e}")
            raise Exception(f"Status check failed: {str(e)}")

    def cancel_payment(self, payment_id: str, idempotence_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel pending payment

        Args:
            payment_id: YooKassa payment ID
            idempotence_key: Idempotence key (auto-generated if not provided)

        Returns:
            Dict with cancellation result

        Raises:
            Exception: If cancellation fails
        """
        try:
            if idempotence_key is None:
                idempotence_key = self.generate_idempotence_key()

            logger.info(f"Canceling payment: payment_id={payment_id}")

            payment = Payment.cancel(payment_id, idempotence_key)

            result = {
                "payment_id": payment.id,
                "status": payment.status,
                "canceled": payment.status == "canceled"
            }

            logger.info(f"Payment canceled: payment_id={payment_id}, status={payment.status}")
            return result

        except Exception as e:
            logger.error(f"Failed to cancel payment: {e}")
            raise Exception(f"Payment cancellation failed: {str(e)}")

    def verify_webhook_ip(self, ip_address: str) -> bool:
        """
        Verify that webhook request comes from YooKassa servers

        Args:
            ip_address: IP address of webhook request

        Returns:
            True if IP is valid YooKassa IP
        """
        # YooKassa webhook IPs (from documentation)
        valid_ip_prefixes = [
            "185.71.76.",
            "185.71.77.",
            "77.75.153.",
            "77.75.156.",
            "77.75.154."
        ]

        # Simple IP validation
        for prefix in valid_ip_prefixes:
            if ip_address.startswith(prefix):
                return True

        logger.warning(f"Webhook from invalid IP: {ip_address}")
        return False

    def process_webhook_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process webhook notification from YooKassa

        Args:
            notification_data: Webhook notification data

        Returns:
            Dict with processed notification:
                - event: Event type (payment.succeeded, payment.canceled, etc.)
                - payment_id: YooKassa payment ID
                - status: Payment status
                - amount: Payment amount
                - metadata: Payment metadata
        """
        try:
            event = notification_data.get('event')
            payment_object = notification_data.get('object', {})

            logger.info(f"Processing webhook notification: event={event}, payment_id={payment_object.get('id')}")

            result = {
                "event": event,
                "payment_id": payment_object.get('id'),
                "status": payment_object.get('status'),
                "amount": Decimal(payment_object.get('amount', {}).get('value', 0)),
                "currency": payment_object.get('amount', {}).get('currency'),
                "metadata": payment_object.get('metadata'),
                "paid": payment_object.get('paid', False)
            }

            return result

        except Exception as e:
            logger.error(f"Failed to process webhook notification: {e}")
            raise Exception(f"Webhook processing failed: {str(e)}")
