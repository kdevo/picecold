import json
import subprocess


class ElectrumError(Exception):
    def __init__(self, message):
        self.message = message


class ElectrumStartError(ElectrumError):
    pass


class TransactionReadError(ElectrumError):
    pass


class ElectrumSigner:
    def __init__(self, path='electrum'):
        self._path = path
        self._json_tx = None

    @property
    def last_raw_tx(self):
        return self._json_tx

    @staticmethod
    def _convert_satoshi(sat):
        return float(sat) / 10.0 ** 8

    def deserialize_transaction(self, path_txn, convert_to_btc=True):
        try:
            out = subprocess.check_output("cat \"{path_txn}\" | {path_elec} deserialize -"
                                          .format(path_txn=path_txn, path_elec=self._path),
                                          shell=True, universal_newlines=True)
            self._json_tx = json.loads(out)
            try:
                tx_parts = []
                for tx in self._json_tx['outputs']:
                    tx_parts.append((tx['address'],
                                     self._convert_satoshi(tx['value']) if convert_to_btc else tx['value']))
                return tx_parts
            except KeyError:
                raise IOError("Transaction file does not seem to be valid or does not have a compatible format.")
        except IOError:
            raise IOError("Unable to read transaction file. Path: " + path_txn)
        except subprocess.CalledProcessError:
            raise ElectrumStartError("Could not start electrum. Path: " + self._path)

    def sign_transaction(self, path_txn, path_signed_txn, password=""):
        try:
            signed_text = subprocess.check_output("cat \"{path_txn}\" | {path_elec} signtransaction - {password}"
                                                  .format(path_txn=path_txn, path_elec=self._path,
                                                          password="" if password == "" else "-W " + password),
                                                  shell=True, universal_newlines=True)
            with open(path_signed_txn, 'x') as signed_file:
                signed_file.write(signed_text)
                return True
        except IOError as io_err:
            print(io_err)
            raise IOError("Unable to sign. Path: {0}. Details: {1}".format(path_txn, io_err))
        except subprocess.CalledProcessError:
            raise ElectrumStartError("Could not start electrum. Path: " + self._path)
