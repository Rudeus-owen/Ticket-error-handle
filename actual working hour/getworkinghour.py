import json
# import random
# import string
import sys
import boto3
import requests
# import os
# from datetime import date, datetime, time
# from datetime import datetime
# from datetime import timedelta
# import pytz
from boto3.dynamodb.conditions import Key, Attr
import common

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

checkxray = common.getallpatch()
if checkxray == "True":
    patch_all()
dynamodb = boto3.resource('dynamodb')
workinghourTable = dynamodb.Table('kunyekworkinghour')
userOrgTable = dynamodb.Table('UserOrganizations')
userDomainTable = dynamodb.Table('UserDomains')
kunyekroleTable = dynamodb.Table('kunyekrole')
# s3value = common.GetBucketSecret()
# bucketname = common.getbucketname()
# ACCESS_ID = s3value['access_id']
# SECRET_KEY = s3value['secret_key']
# lambda_client = boto3.client("lambda")
# client = boto3.client('s3', aws_access_key_id=ACCESS_ID,
#                       aws_secret_access_key=SECRET_KEY)
# s3 = boto3.resource('s3', aws_access_key_id=ACCESS_ID,
#                     aws_secret_access_key=SECRET_KEY)
# userTable = dynamodb.Table('kunyekusers')

iamurl = common.getiamurl()
# kunyekurl  = common.getkunyekurl()
# headers = {
#     'Access-Control-Allow-Headers': 'Content-Type',
#     'Access-Control-Allow-Origin': '*',
#     'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
# }

requesttypepermission = "008"


def lambda_handler(event, context):
    if event['httpMethod'] == "POST":
        try:
            body = json.loads(event['body'])
            checkuser = common.validateUser(event,body['userid'])
            if checkuser == False:
                body = {
                    'returncode': "200",
                    'status': "Unauthorized Access!"
                }
                return cb(200, body)
            if "userid" not in body or "domainid" not in body or "appid" not in body or 'orgid' not in body:
                body = {
                    'returncode': "200",
                    'status': "Missing Field!"
                }
                return cb(200, body)
            else:
                userid = body['userid']
                appid = body['appid']
                roleid = ""
                if 'roleid' in body:
                    roleid = body['roleid']
                # now_asia = datetime.now(ZoneInfo("Asia/Yangon"))
                orgid = body['orgid']
                domainid = body['domainid']
                userdomaindata = userDomainTable.query(
                    KeyConditionExpression = Key('userid').eq(userid),
                    FilterExpression = Attr('appid').eq(appid) & Attr('domainid').eq(domainid) & Attr('role').eq('200')
                )["Items"]
                if len(userdomaindata) == 0:
                    returncheck = common.checkorgadminandrole(userid,userid,orgid,appid,domainid,roleid,requesttypepermission)
                    userorglist = returncheck['data']
                    if returncheck['valid'] == False:
                        body = {
                            'returncode': "200",
                            'status': "Unauthorized Access"
                        }
                        return cb(200, body)
                    # lastEvaluatedKey = None
                    # userorglist = []
                    # while True:
                    #     if lastEvaluatedKey == None:
                    #         response = userOrgTable.query(
                    #             KeyConditionExpression=Key('userid').eq(userid),
                    #             FilterExpression=Attr('orgid').eq(orgid) & Attr('appid').eq(appid) & Attr('domainid').eq(domainid)
                    #         )
                    #     else:
                    #         response = userOrgTable.query(
                    #             KeyConditionExpression=Key('userid').eq(userid),
                    #             FilterExpression=Attr('orgid').eq(orgid) & Attr('appid').eq(appid) & Attr('domainid').eq(domainid),
                    #             ExclusiveStartKey=lastEvaluatedKey
                    #         )
                    #     # Appending to our resultset list
                    #     userorglist.extend(response['Items'])
                    #     # Set our lastEvlauatedKey to the value for next operation,
                    #     # else, there's no more results and we can exit
                    #     if 'LastEvaluatedKey' in response:
                    #         lastEvaluatedKey = response['LastEvaluatedKey']
                    #     else:
                    #         break
                    # if len(userorglist) == 0:
                    #     body = {
                    #         'returncode': "200",
                    #         'status': "Unauthorized Access"
                    #     }
                    #     return cb(200, body)
                    # else:
                    #     filteradmin = next(filter(lambda x: x['t1'] == "300", userorglist),None)
                    #     if filteradmin == None:
                    #         if roleid == "":
                    #             body = {
                    #                 'returncode': "200",
                    #                 'status': "Unauthorized Access"
                    #             }
                    #             return cb(200, body)
                    #         roleresponse = kunyekroleTable.get_item(
                    #             Key={
                    #                 'orgid': orgid,
                    #                 'roleid': roleid
                    #             }
                    #         )
                    #         if 'Item' not in roleresponse:
                    #             body = {
                    #                 'returncode': "200",
                    #                 'status': "Unauthorized Access"
                    #             }
                    #             return cb(200, body)
                    #         filterrequestsort = next(filter(lambda x: x == roleid and requesttypepermission in roleresponse["Item"]['permission'], userorglist[0]['rolelist']),None)
                    #         if filterrequestsort == None:
                    #             body = {
                    #                 'returncode': "200",
                    #                 'status': "Unauthorized Access"
                    #             }
                    #             return cb(200, body)
                    # userorglist = userOrgTable.query(
                    #     KeyConditionExpression=Key('userid').eq(userid),
                    #     FilterExpression=Attr('orgid').eq(orgid) & Attr('appid').eq(appid)
                    # )["Items"]
                    # if len(userorglist) == 0:
                    #     body = {
                    #         'returncode': "200",
                    #         'status': "Unauthorized Access!"
                    #     }
                    #     return cb(200, body)
                
                workinghourdata = workinghourTable.query(
                    KeyConditionExpression=Key('orgid').eq(orgid),
                    FilterExpression= Attr('domainid').eq(domainid) & Attr('appid').eq(appid)
                )["Items"]
                
                #Ensure correct calculation and return
                total_working_hours = sum([item['workinghours'] for item in workinghourdata])

                if len(workinghourdata) > 0:
                    response = {
                        'returncode': "300",
                        'whlist': workinghourdata,
                        'total_working_hours':total_working_hours
                    }
                    return cb(200, response)
                else:
                    response = {
                        'returncode': "300",
                        'whlist': []
                    }
                    return cb(200, response)

        except Exception as e:
            body = json.loads(event['body'])

            lineno = '{} on line {}'.format(
                e, sys.exc_info()[-1].tb_lineno)

            return common.AddServerErrorLog(functionname="getworkinghour", body=body, lineno=lineno)

def cb(statuscode, body):
    return {
        'statusCode': int(statuscode),
        'headers': common.headers,
        'body': json.dumps(body)
    }


def cb1(statuscode, body):
    return {
        'statusCode': int(statuscode),
        'headers': common.headers,
        'body': body
    }
