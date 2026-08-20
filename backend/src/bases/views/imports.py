from datetime import datetime

from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import src.core.models as models
from src.core import forms
from src.services.phone import (
    PhoneCreateService,
    PhoneUpdateService,
    PhoneDeleteService,
    PhoneSellService,
)
from src.services.accessory import (
    AccessoryCreateService,
    AccessoryUpdateService,
    AccessoryDeleteService,
    AccessorySellService,
)
from src.services.debt import (
    DebtCreateService,
    DebtUpdateService,
    DebtDeleteService,
    DebtPaymentCreateService,
    DebtPaymentUpdateService,
    DebtPaymentDeleteService,
)
from src.services.expense import (
    ExpenseCreateService,
    ExpenseUpdateService,
    ExpenseDeleteService,
)
from src.services.salary import (
    SalaryCreateService,
    SalaryUpdateService,
    SalaryDeleteService,
)
from src.services.extra_profit import (
    ExtraProfitCreateService,
    ExtraProfitUpdateService,
    ExtraProfitDeleteService,
)
from src.services.branch import (
    BranchCreateService,
    BranchUpdateService,
    BranchDeleteService,
)
from src.services.user import (
    UserCreateService,
    UserUpdateService,
    UserDeleteService,
)
from src.services.dashboard import DashboardService


from src.frontend.admin.mixins import AdminRequiredMixin
from src.frontend.cashier.mixins import CashierRequiredMixin
