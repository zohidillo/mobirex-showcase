from src.frontend.crud.phone.forms import PhoneCreateForm, PhoneUpdateForm, PhoneSellForm
from src.frontend.crud.accessory.forms import (
    AccessoryCreateForm,
    AccessoryUpdateForm,
    AccessorySellForm,
)
from src.frontend.crud.debt.forms import (
    DebtCreateForm,
    DebtUpdateForm,
    DebtPaymentForm,
)
from src.frontend.crud.expense.forms import (
    ExpenseForm,
    SalaryForm,
)
from src.frontend.crud.extra_profit.forms import (
    ExtraProfitForm,
)
from src.frontend.admin.branch.forms import BranchForm
from src.frontend.admin.user.forms import UserForm
from src.frontend.admin.phone_category.forms import PhoneCategoryForm
from src.frontend.admin.accessory_category.forms import AccessoryCategoryForm
from src.frontend.cashier.forms import PaymentForm

__all__ = [
    "PhoneCreateForm",
    "PhoneUpdateForm",
    "PhoneSellForm",
    "AccessoryCreateForm",
    "AccessoryUpdateForm",
    "AccessorySellForm",
    "DebtCreateForm",
    "DebtUpdateForm",
    "DebtPaymentForm",
    "ExpenseForm",
    "SalaryForm",
    "ExtraProfitForm",
    "BranchForm",
    "UserForm",
    "PhoneCategoryForm",
    "AccessoryCategoryForm",
    "PaymentForm",
]
