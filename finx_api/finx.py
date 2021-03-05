#! Python
import os
import json
import dotenv
import requests


class FinX:
	api_url = 'https://sandbox.finx.io/api/'
	session = None
	request_body = {}

	def __init__(self, api_key=None, json_path=None, env_path=None):
		"""
		Client constructor accepts 4 distinct methods for securely passing credentials:
		1. api_key: string literal
		2. json_path: path to JSON file containing the key "finx_api_key"
		3. env_path: path to .env file containing the key "finx_api_key"
		4. environment variable: exported environment variable named "api_key". Default if no args passed
		"""
		if api_key is not None:
			self.api_key = api_key
		elif json_path is not None:
			config = json.load(json_path)
			self.api_key = config['api_key']
		else:
			if env_path is not None:
				dotenv.load_dotenv(env_path)
			self.api_key = os.getenv('API_KEY')
		assert self.api_key is not None
		self.session = requests.session()

	def dispatch(self):
		return self.session.post(self.api_url, data=self.request_body).json()

	def get_api_methods(self):
		"""
		List API methods with parameter specifications
		"""
		self.request_body = {
			'finx_api_key': self.api_key,
			'api_method': 'list_api_functions'
		}
		return self.dispatch()

	def get_security_reference_data(self, security_id, as_of_date=None):
		"""
		Security reference function
		:param security_id: string
		:param as_of_date: string as YYYY-MM-DD (optional)
		:return:
		"""
		self.request_body = {
			'finx_api_key': self.api_key,
			'api_method': 'security_reference',
			'security_id': security_id,
			'as_of_date': as_of_date
		}
		return self.dispatch()

	def get_security_analytics(self, security_id,
	                           as_of_date=None,
	                           price=100,
	                           volatility=None,
	                           yield_shift=None,
	                           shock_in_bp=None,
	                           horizon_months=None,
	                           income_tax=None,
	                           cap_gain_short_tax=None,
	                           cap_gain_long_tax=None):
		"""
		Security analytics function
		:param security_id: string (required)
		:param as_of_date: string as YYYY-MM-DD (optional)
		:param price: float (optional)
		:param volatility: float (optional)
		:param yield_shift: int (basis points, optional)
		:param shock_in_bp: int (basis points, optional)
		:param horizon_months: uint (optional)
		:param income_tax: float (optional)
		:param cap_gain_short_tax: float (optional)
		:param cap_gain_long_tax: float (optional)
		"""
		self.request_body = {
			'finx_api_key': self.api_key,
			'api_method': 'security_analytics',
			'security_id': security_id,
			'as_of_date': as_of_date,
			'price': price,
			'volatility': volatility,
			'yield_shift': yield_shift,
			'shock_in_bp': shock_in_bp,
			'horizon_months': horizon_months,
			'income_tax': income_tax,
			'cap_gain_short_tax': cap_gain_short_tax,
			'cap_gain_long_tax': cap_gain_long_tax
		}
		return self.dispatch()

	def get_security_cash_flows(self, security_id, as_of_date=None, price=100, shock_in_bp=None):
		"""
		Security cash flows function
		:param security_id: string
		:param as_of_date: string as YYYY-MM-DD (optional)
		:param price: float (optional)
		:param shock_in_bp: int (optional)
		"""
		self.request_body = {
			'finx_api_key': self.api_key,
			'api_method': 'security_cash_flows',
			'security_id': security_id,
			'as_of_date': as_of_date,
			'price': price,
			'shock_in_bp': shock_in_bp
		}
		return self.dispatch()
