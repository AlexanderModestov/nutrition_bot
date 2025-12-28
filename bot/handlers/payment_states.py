from aiogram.fsm.state import State, StatesGroup

class PaymentStates(StatesGroup):
    """FSM states for payment flow"""
    selecting_product = State()
    confirming_payment = State()
    awaiting_payment = State()
    payment_completed = State()
