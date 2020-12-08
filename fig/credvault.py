##fileEnc.py
##python3.7
##Work@Crowdstrike

#fileEnc.py will encode streaming credentials for the CID
#as well as decode them

# import pickle
import os
import boto3
# from simplecrypt import encrypt, decrypt
import urllib


class CredVault():

    def __init__(self, logger):
        self.region = urllib.request.urlopen('http://169.254.169.254/latest/meta-data/placement/availability-zone').read().decode()[:-1]
        self.logger = logger

    def _getParameter(self, param_name):
        """
        This function reads a secure parameter from AWS' SSM service.
        The request must be passed a valid parameter name, as well as
        temporary credentials which can be used to access the parameter.
        The parameter's value is returned.
        """
        # Create the SSM Client
        ssm = boto3.client('ssm',
                           region_name=self.region
                           )

        # Get the requested parameter
        response = ssm.get_parameters(
            Names=[
                param_name,
            ],
            WithDecryption=True
        )
        # Store the credentials in a variable
        credentials = response['Parameters'][0]['Value']
        return credentials

    def get(self):
        try:
            self.KEY = self._getParameter('KEY')
            self.UUID = self._getParameter('UUID')
            self.APP_ID = "FIG-SH" + self._getParameter('APP_ID')
            self.PRIORITY = self._getParameter('PRIORITY')
            # self.group = [encrypt(self.k, self.KEY), encrypt(self.k, self.UUID), encrypt(self.k, self.APP_ID), encrypt(self.k, self.PRIORITY)]
            return [self.KEY, self.UUID, self.APP_ID, self.PRIORITY]
        except Exception as error:
            self.logger.errorWrite("Error \n{}\n fetching data from Parameter Store".format(error))
            os._exit(0)
