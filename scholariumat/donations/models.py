import datetime
import logging
import uuid

from django.db import models
from django.conf import settings

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

from framework.behaviours import CommentAble
from .payment import Payment


logger = logging.getLogger(__name__)


class DonationLevel(TitleSlugDescriptionModel):
    amount = models.SmallIntegerField(unique=True)

    @classmethod
    def get_level_by_amount(cls, amount):
        level = cls.objects.filter(amount__lte=amount).order_by('-amount')
        if level:
            return level[0]
        else:
            logger.info("No level available for {}".format(amount))

    @classmethod
    def get_lowest_amount(cls):
        level = cls.objects.all().order_by('-amount')
        return level[0].amount if level else None

    class Meta:
        verbose_name = 'Spendenstufe'
        verbose_name_plural = 'Spendenstufen'

    def __str__(self):
        return '{}: {}'.format(self.amount, self.title)


class PaymentMethod(TitleSlugDescriptionModel):

    def get_approval_url(self, amount):
        """Creates payment and returns approval url."""
        payment = Payment(self)
        payment.create(amount)
        return payment.approval_url

    def execute_payment(self, request):
        """
        Takes request object returned from approval urls, containing necessary execution information.
        Executes/Checks payment and creates Donation.
        """
        payment = Payment(self)
        if payment.execute(request):
            donation_kwargs = {
                'payment_id': payment.id,
                'payment_method': self
            }
            payment.user.donate(payment.amount, donation_kwargs)
            return True

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Zahlungsmethode'
        verbose_name_plural = 'Zahlungsmethoden'


class Donation(CommentAble, TimeStampedModel):
    """Enables user to use services according to active donation level."""
    @staticmethod
    def _default_expiration():
        return datetime.date.today() + datetime.timedelta(days=settings.DONATION_PERIOD)

    @staticmethod
    def _default_payment_id():
        return uuid.uuid4().hex.upper()

    profile = models.ForeignKey('users.Profile', on_delete=models.CASCADE)
    amount = models.IntegerField()
    date = models.DateField(auto_now_add=True)
    expiration = models.DateField(default=_default_expiration.__func__)
    payment_method = models.ForeignKey(PaymentMethod, null=True, blank=True, on_delete=models.SET_NULL)
    review = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=50, default=_default_payment_id.__func__)

    @property
    def level(self):
        return DonationLevel.get_level_by_amount(self.amount)

    # def execute(self):
    #     """Refills users balance and marks donation as executed."""
    #     if not self.executed:
    #         self.profile.refill(self.level.amount)
    #         self.executed = True
    #         self.save()
    #         logger.debug('{} donated and is now {}.'.format(self.profile, self.level.title))
    #         return True

    # def get_approval_url(self):
    #     """Creates payment, sets payment id and returns approval url."""
    #     if not self.payment_method:
    #         logger.error("Can't get approval url. No payment method")
    #         return None
    #     payment = self.payment_method.create(self.level)
    #     if payment.id:
    #         self.payment_id = payment.id
    #         self.save()
    #         return payment.approval_url

    # def pay(self, request):
    #     """
    #     Takes request object returned from approval urls, containing necessary execution information.
    #     Executes payment and sets exicuted to True if successfull.
    #     """
    #     if not self.payment_method:
    #         logger.error("Can't execute payment. No payment method")
    #     elif self.payment_method.execute(self.payment_id, request):
    #         return self.execute()

    def __str__(self):
        return '%s: %s (%s)' % (self.profile.name, self.level.title, self.date)

    class Meta:
        verbose_name = 'Unterstützung'
        verbose_name_plural = 'Unterstuetzungen'
