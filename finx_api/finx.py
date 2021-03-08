#! Python
import os
import yaml
import dotenv
import requests


class FinX:
	__api_url = None
	__request_body = {}
	session = None

	def __init__(self, **kwargs):
		"""
		Client constructor accepts 2 distinct methods for passing credentials named FINX_API_KEY and FINX_API_ENDPOINT
		1. config_path: path to YAML file
		2. env_path: path to .env file
		If yaml_path not passed, loads env_path (if passed) then checks environment variables
		"""
		yaml_path = kwargs.get('yaml_path')
		if yaml_path is not None:
			config = yaml.safe_load(open(yaml_path))
			self.__api_key = config.get('FINX_API_KEY')
			self.__api_url = config.get('FINX_API_ENDPOINT')
		else:
			env_path = kwargs.get('env_path')
			if env_path is not None:
				try:
					dotenv.load_dotenv(env_path)
				except:
					print(f'Could not load .env file at {env_path}')
			self.__api_key = os.getenv('FINX_API_KEY')
			self.__api_url = os.getenv('FINX_API_ENDPOINT')
		if self.__api_key is None:
			raise Exception('API key not found')
		if self.__api_url is None:
			self.__api_url = 'https://sandbox.finx.io/api/'
		self.session = requests.session()

	def dispatch(self):
		return self.session.post(self.__api_url, data=self.__request_body).json()

	def get_api_methods(self):
		"""
		List API methods with parameter specifications
		"""
		self.__request_body = {
			'finx_api_key': self.__api_key,
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
		self.__request_body = {
			'finx_api_key': self.__api_key,
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
		self.__request_body = {
			'finx_api_key': self.__api_key,
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
		self.__request_body = {
			'finx_api_key': self.__api_key,
			'api_method': 'security_cash_flows',
			'security_id': security_id,
			'as_of_date': as_of_date,
			'price': price,
			'shock_in_bp': shock_in_bp
		}
		return self.dispatch()
