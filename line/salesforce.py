import os
from simple_salesforce import (Salesforce, SalesforceAuthenticationFailed,
                               SalesforceError, SFType, SalesforceLogin)
from line.logger import logger
from django.conf import settings


class SfConnecter(object):
    """
    Salesforce APIに接続
    """
    def __init__(self):
        """Salesforce APIに接続設定"""
        try:
            self.session_id, self.instance = SalesforceLogin(
                username=os.environ.get('SF_EMAIL'),
                password=os.environ.get('SF_PASSWORD'),
                security_token=os.environ.get('SF_TOKEN', ''),
                sandbox=os.environ.get('SF_SANDBOX', 'False') == 'True')
            self.sf = Salesforce(
                username=os.environ.get('SF_EMAIL'),
                password=os.environ.get('SF_PASSWORD'),
                security_token=os.environ.get('SF_TOKEN', ''),
                sandbox=os.environ.get('SF_SANDBOX', 'False') == 'True')
        except SalesforceAuthenticationFailed as ex:
            logger.info(ex)
            pass

        except Exception as ex:
            logger.info(ex)
            pass

    def sf_query(self, sql: str) -> [int, dict]:
        """SQLでデータを取得"""
        try:
            results = self.sf.query(sql)
            return [200, results['records']]

        except SalesforceError as ex:
            logger.info(ex)
            return [500, {'message: ' + str(ex.content)}]

        except Exception as ex:
            logger.info(ex)
            return [500, {'message: ' + str(ex)}]

    def sf_get_by_id(self, api: str, sfid: str) -> [int, dict]:
        """SFIDでデータ取得"""
        try:
            api_query = SFType(api, self.session_id, self.instance)
            results = api_query.get(sfid)
            return [200, results]

        except SalesforceError as ex:
            logger.info(ex.content)
            return [ex.status, ex.content]

        except Exception as ex:
            logger.info(ex)
            return [500, {'message: ' + str(ex)}]

    def sf_create(self, api: str, data: dict) -> [int, dict]:
        """作成"""
        try:
            api_query = SFType(api, self.session_id, self.instance)
            results = api_query.create(data)
            if results['success'] is False:
                raise Exception(results['error'])
            if settings.TESTING:
                logger.info(results)
                self.sf_delete(api, results['id'])
                return [200, results]
            return [200, results]

        except SalesforceError as ex:
            logger.info(ex.content)
            return [ex.status, ex.content]

        except Exception as ex:
            logger.info(ex)
            return [500, {'message: ' + str(ex)}]

    def sf_delete(self, api: str, sfid: str) -> [int, dict]:
        """削除"""
        try:
            api_query = SFType(api, self.session_id, self.instance)
            results = api_query.delete(sfid)
            return [200, results]

        except SalesforceError as ex:
            logger.info(ex)
            return [500, {'message: ' + str(ex.content)}]

        except Exception as ex:
            logger.info(ex)
            return [500, {'message: ' + str(ex)}]

    def sf_update(self, api: str, sfid: str, data: dict) -> [int, dict]:
        """更新"""
        try:
            api_query = SFType(api, self.session_id, self.instance)
            results = api_query.update(sfid, data)
            if results != 204:
                raise Exception(results['error'])
            return [200, results]

        except SalesforceError as ex:
            logger.info(ex.content)
            return [ex.status, ex.content]

        except Exception as ex:
            logger.info(ex)
            return [500, {'message: ' + str(ex)}]


class FaqApi(SfConnecter):
    """
    SF ナレッジ用のAPI
    """
    def get_all(self) -> [int, dict]:
        """データ取得"""
        sql = ("SELECT Field1__c, Field2__c FROM FAQ__kav WHERE "
               "PublishStatus='Online' AND Language='ja'")
        return self.sf_query(sql)

    def get_faq(self, question) -> str or None:
        sql = ("SELECT Field1__c, Field2__c FROM FAQ__kav "
               "WHERE PublishStatus='Online' AND Language='ja' AND "
               "Title='{0}'").format(question)

        status, data = self.sf_query(sql)
        if status != 200:
            return None
        try:
            return data[0].get('Field2__c')
        except:
            return None


class DictApi(SfConnecter):
    """
    SF 辞書用のAPI
    """
    def get_all(self) -> [int, dict]:
        """データ取得"""
        sql = ("SELECT Proper_Noun__c, Attribute__c, Reading__c FROM"
               " Dictionary__c WHERE Type__c='LINE'")
        return self.sf_query(sql)


class BotApi(SfConnecter):
    """
    SF ボット応答用のAPI
    """
    def get_all(self) -> [int, dict]:
        """データ取得"""
        sql = ("SELECT References__c, Question_Sentence__c, Access_Point__c, "
               "Reply_Sentence__c FROM Bot_Response__c WHERE Type__c='LINE'")
        return self.sf_query(sql)


class ContactApi(SfConnecter):
    """
    SF 担当者用のAPI
    """
    def get_by_line_id(self, line_id):
        sql = ("SELECT Id, Name, Lastname, LINE_ID__c FROM Contact "
               "WHERE LINE_ID__c='{0}'").format(line_id)
        return self.sf_query(sql)

    def get_query_by_line_id(self, query, line_id):
        try:
            sql = ("SELECT Id, Name, {query}, LINE_ID__c FROM"
                   " Contact WHERE LINE_ID__c='{line_id}'").format(
                query=query, line_id=line_id)
            _, data = self.sf_query(sql)
            return data[0]
        except Exception as ex:
            print(ex)
            pass

    def get_by_email(self, email):
        sql = ("SELECT Id, Name, Lastname, Email FROM Contact "
               "WHERE Email='{0}'").format(email)
        return self.sf_query(sql)

    def create(self, data: dict) -> [int, dict]:
        """データ作成"""
        return self.sf_create('Contact', data)

    def register(self, email: str, line_id: str) -> [int, dict]:
        """データ作成"""
        status, sf_data = self.get_by_email(email)

        if sf_data[0].get('Id') is None:
            return [404, {'message': 'DoesNotData'}]

        return self.sf_update('Contact', sf_data[0].get('Id'), {
            'LINE_ID__c': line_id
        })
