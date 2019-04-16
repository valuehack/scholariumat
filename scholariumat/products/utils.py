import requests
from requests.auth import HTTPBasicAuth
import xml.dom.minidom
import logging

from django.conf import settings


logger = logging.getLogger(__name__)


class SofortPayment(object):
    """
    Idee der Sofort-Api-Schnittstelle:
        mit jedem Api-Aufruf müssen Authentifizierungsdaten mitgeschickt werden
        die sind aus dem Klassenattribut verfügbar
        den Aufrufen sind xml-Dateien anzuhängen, die die Daten enthalten
        die Zahlung hat eine id bei sofort und gehört zu einem payment in der lokalen DB
        neben den Daten der Zahlung (Betrag, Betreff, etc) akzeptiert die api drei urls,
            die die Defaultwerte aus dem Sofort-Kundenkonto überschreiben:
            für die Weiterleitung des Kunden bei Erfolg, bei Fehler, und für
            die Benachrichtigung vom Shop bei jeglicher späteren Statusänderung
    """
    url = 'https://api.sofort.com/api/xml'
    pw = settings.SOFORT_KEY
    headers = {
        'Content-Type': 'application/xml',
        'Accept': 'application/xml',
    }
    project_id = settings.SOFORT_PROJECT_ID
    success_url = 'https://scholarium.at/'
    abort_url = 'https://scholarium.at/'
    creation_template = """<?xml version="1.0" encoding="UTF-8" ?>
<multipay>
      <project_id>{project_id}</project_id>
      <interface_version>testilja</interface_version>
      <amount>{amount}</amount>
      <currency_code>EUR</currency_code>
      <beneficiary>
         <identifier>scholarium</identifier>
         <country_code>AT</country_code>
      </beneficiary>
      <reasons>
            <reason>{reason}</reason>
            <reason>-TRANSACTION-</reason>
      </reasons>
      <user_variables>
            <user_variable>spam</user_variable>
      </user_variables>
      <success_url>{success_url}</success_url>
      <success_link_redirect>1</success_link_redirect>
      <abort_url>{abort_url}</abort_url>
      <notification_urls>
            <notification_url>https://scholarium.at/spam</notification_url>
      </notification_urls>
      <su />
</multipay>
"""

    def creation_string(self, **kwargs):
        params = dict(
            amount=75.0,
            reason='Spende scholarium.at',
            success_url=self.success_url,
            abort_url=self.abort_url,
            project_id=self.project_id,
        )
        params.update(kwargs)
        return self.creation_template.format(**params)

    def __init__(self, **kwargs):
        """ Initializes new payment """
        r = self.post(self.creation_string(**kwargs))

        self.init_response = r
        # this is not sooo robust, but should work if the api doesnt change^^:
        self.return_url = r.text.split('payment_url')[1][1:-2]
        self.sofort_id = r.text.split('<transaction>')[1].split('</transaction>')[0]

        return None

    @classmethod
    def check_status(cls, sofort_id):
        """ Ruft die Daten zu einer Transaktions-id ab

        theoretisch kann man statt nach der Nummer auch nach allen Transaktionen
        in einem Zeitraum fragen, das habe ich aber nicht implementiert. """

        response = cls.post("""<?xml version="1.0" encoding="UTF-8" ?>
            <transaction_request version="2">
                <transaction>{sofort_id}</transaction>
            </transaction_request>""".format(sofort_id=sofort_id))

        logger.info(xml.dom.minidom.parseString(response.text).toprettyxml())
        return response

    @classmethod
    def post(cls, text):
        """ Anfrage an die Sofort-Api """
        r = requests.post(
            cls.url,
            auth=HTTPBasicAuth('120628', cls.pw),
            headers=cls.headers,
            data=text,
        )

        return r
