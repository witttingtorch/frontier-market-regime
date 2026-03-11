"""Central Bank of Azerbaijan data collector."""

import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CBACollector:
    """CBA SOAP API client — no API key required."""
    
    BASE_URL = "http://api.cba.am/exchangerates.asmx"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'http://www.cba.am/ExchangeRatesByDate'
        })
    
    def _build_soap_request(self, date: datetime) -> str:
        """Build SOAP request for exchange rates by date."""
        return f"""<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                       xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                       xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <soap:Body>
            <ExchangeRatesByDate xmlns="http://www.cba.am/">
              <date>{date.strftime('%Y-%m-%d')}</date>
            </ExchangeRatesByDate>
          </soap:Body>
        </soap:Envelope>"""
    
    def get_rates_by_date(self, date: Optional[datetime] = None) -> pd.DataFrame:
        """Fetch exchange rates for specific date."""
        if date is None:
            date = datetime.now()
        
        try:
            response = self.session.post(
                self.BASE_URL,
                data=self._build_soap_request(date),
                timeout=30
            )
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            rates = []
            
            for rate in root.findall('.//{http://www.cba.am/}Rate'):
                iso = rate.find('{http://www.cba.am/}ISO').text
                amount = int(rate.find('{http://www.cba.am/}Amount').text)
                rate_value = float(rate.find('{http://www.cba.am/}Rate').text)
                
                rates.append({
                    'date': date,
                    'currency': iso,
                    'rate': rate_value,
                    'amount': amount,
                    'azn_per_unit': rate_value / amount
                })
            
            df = pd.DataFrame(rates)
            logger.info(f"CBA: Fetched {len(df)} rates for {date.date()}")
            return df
            
        except Exception as e:
            logger.error(f"CBA Error: {e}")
            return pd.DataFrame()
    
    def get_usd_history(self, days: int = 30) -> pd.DataFrame:
        """Get USD/AZN rates for last N days."""
        end = datetime.now()
        start = end - timedelta(days=days)
        
        all_rates = []
        current = start
        
        while current <= end:
            daily = self.get_rates_by_date(current)
            if not daily.empty:
                usd = daily[daily['currency'] == 'USD']
                if not usd.empty:
                    all_rates.append(usd.iloc[0].to_dict())
            current += timedelta(days=1)
        
        df = pd.DataFrame(all_rates)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').set_index('date')
        
        return df


if __name__ == "__main__":
    cba = CBACollector()
    rates = cba.get_usd_history(days=10)
    print(rates[['currency', 'azn_per_unit']])
