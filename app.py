from flask import Flask, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

class RugCheckData:
    def __init__(self, data: dict):
        for key, value in data.items():
            if isinstance(value, dict):
                value = RugCheckData(value)
            elif isinstance(value, list):
                value = [RugCheckData(item) if isinstance(item, dict) else item for item in value]
            setattr(self, key, value)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def to_dict(self):
        def convert(value):
            if isinstance(value, RugCheckData):
                return value.to_dict()
            elif isinstance(value, list):
                return [convert(item) for item in value]
            return value
        return {key: convert(value) for key, value in self.__dict__.items()}

class RugCheck:
    def __init__(self, token_address: str):
        self.token_address = token_address
        self._wrapped_data = RugCheckData(self.__fetch_report())
        for key, value in self._wrapped_data.__dict__.items():
            setattr(self, key, value)

    def __fetch_data(self, url: str) -> dict:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url=url, headers=headers)
        return response.json()

    def __fetch_report(self):
        return self.__fetch_data(f'https://api.rugcheck.xyz/v1/tokens/{self.token_address}/report')

    @property
    def result(self) -> str:
        return 'Good' if self.score < 1000 else 'Warning' if self.score < 5000 else 'Danger'

    @property
    def summary(self) -> dict:
        return {
            'name': self.tokenMeta.name,
            'symbol': self.tokenMeta.symbol,
            'rugged': self.rugged,
            'result': self.result,
            'riskScore': self.score,
            'mint': self.mint,
            'totalMarketLiquidity': self.totalMarketLiquidity
        }

@app.route('/solana/<string:address>', methods=['GET'])
def solana_check(address):
    try:
        check = RugCheck(address)
        return jsonify(check.summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def root():
    return jsonify({"status": "RugCheck Proxy running"})
