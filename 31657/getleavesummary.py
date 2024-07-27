import json
import boto3
# import requests
import sys
from datetime import datetime
import common
# import datetime as date1
from boto3.dynamodb.conditions import Key, Attr
# from backports.zoneinfo import ZoneInfo
# import random
# import string
# import time
# from urllib.parse import urlencode
# from urllib.request import urlopen


from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

checkxray = common.getallpatch()
if checkxray == "True":
    patch_all()
dynamodb = boto3.resource('dynamodb')
bucketname = common.getbucketname()
# leavetypeTable = dynamodb.Table('kunyekleavetype')
# claimtypeTable = dynamodb.Table('kunyekclaimtype')
# currencyTable = dynamodb.Table('kunyekcurrency')
requestTable = dynamodb.Table('kunyekrequest')
entitlementTable = dynamodb.Table('kunyekentitlement')
userOrgTable = dynamodb.Table('UserOrganizations')
# templateTable = dynamodb.Table('kunyektemplate')
calendarTable = dynamodb.Table('kunyekcalendar')
# userTable = dynamodb.Table('kunyekusers')
requesttypeTable = dynamodb.Table('kunyekrequesttype')
orgtable = dynamodb.Table('Organizations')
# hierarchyTable = dynamodb.Table('Hierarchy')
# kunyekroleTable = dynamodb.Table('kunyekrole')
openingTable = dynamodb.Table('kunyekopening')
memberTypeTable = dynamodb.Table('MemberType')
UserIDMappingTable = dynamodb.Table('UserIDMapping')
s3value = common.GetBucketSecret()
bucketname = common.getbucketname()
ACCESS_ID = s3value['access_id']
SECRET_KEY = s3value['secret_key']
# lambda_client = boto3.client("lambda")
client = boto3.client('s3', aws_access_key_id=ACCESS_ID,
                      aws_secret_access_key=SECRET_KEY)
# s3 = boto3.resource('s3', aws_access_key_id=ACCESS_ID,
#                     aws_secret_access_key=SECRET_KEY)

iamurl = common.getiamurl()
# kunyekurl = common.getkunyekurl()

# apiid = "00001"
requesttypepermission = "009"
# headers = {
#     'Access-Control-Allow-Headers': 'Content-Type',
#     'Access-Control-Allow-Origin': '*',
#     'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
# }


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
            userid = body['userid']
            orgid = body['orgid']
            startdate = body['startdate']
            enddate = body['enddate']
            domainid = body['domainid']
            appid = body['appid']
            roleid=body.get("roleid","")
            year=body.get("year","")
            division = body.get("division", "")
            department = body.get("department", "")
            teamid = body.get("teamid", "")
            costcenter = body.get("costcenter", "")
            subdivision = body.get("subdivision", "")
            calendarid = body.get("calendarid","")
            activestatus = body.get("activestatus","")
            if year != "":
                startdate = year+"01"+"01"
                enddate = year+"12"+"31"
            if roleid != "":
                returncheck = common.checkorgadminandrole(userid,userid,orgid,appid,domainid,roleid,requesttypepermission)
                # userorglist = returncheck['data']
                if returncheck['valid'] == False:
                    body = {
                        'returncode': "200",
                        'status': "Unauthorized Access!"
                    }
                    return cb(200, body)
            else:
                userorglist = []
                lastEvaluatedKey = None
                while True:
                    kwargs = {'FilterExpression': Attr('orgid').eq(orgid) & Attr('appid').eq(appid) & Attr('domainid').eq(domainid) & (Attr('t1').eq("300") | Attr('hradmin').eq("700")) }
                    if lastEvaluatedKey is not None:
                        kwargs |= {'ExclusiveStartKey': lastEvaluatedKey}

                    res = userOrgTable.query(KeyConditionExpression=Key('userid').eq(userid),**kwargs,ProjectionExpression="userid")
                    userorglist += res['Items']

                    if 'LastEvaluatedKey' in res:
                        lastEvaluatedKey = res['LastEvaluatedKey']
                    else:
                        break
                if len(userorglist) == 0:
                    body = {
                        'returncode': "200",
                        'status': "Unauthorized Access!"
                    }
                    return cb(200, body)
            filterdata = Attr('employeeid').ne("")
            if division != "":
                filterdata &= Attr('division').eq(division)
            if department != "":
                filterdata &= Attr('department').eq(department)
            if teamid != "":
                filterdata &= Attr('teamid').eq(teamid)
            if costcenter != "":
                filterdata &= Attr('costcenter').eq(costcenter)
            if subdivision != "":
                filterdata &= Attr('subdivision').eq(subdivision)
            userorglist = []
            lastEvaluatedKey = None
            while True:
                kwargs = {"IndexName": "orgid-index", 
                            'FilterExpression': filterdata}
                if lastEvaluatedKey is not None:
                    kwargs |= {'ExclusiveStartKey': lastEvaluatedKey}

                res = userOrgTable.query(KeyConditionExpression=Key('orgid').eq(orgid),
                                            **kwargs, ProjectionExpression='userid, employeeid, username, transactiontype, division, department, teamid, joineddate, #dynobase_type, typeid, post, costcenter',ExpressionAttributeNames={"#dynobase_type": "type"})
                userorglist += res['Items']

                if 'LastEvaluatedKey' in res:
                    lastEvaluatedKey = res['LastEvaluatedKey']
                else:
                    break
            
            requesttypeall = []
            lastEvaluatedKey = None
            while True:
                kwargs = {'FilterExpression': Attr('orgid').eq(orgid) & Attr('parentid').eq("NCMLEIWHRNVIE") & Attr('domainid').eq(domainid) & Attr('appid').eq(appid)}
                if lastEvaluatedKey is not None:
                    kwargs |= {'ExclusiveStartKey': lastEvaluatedKey}

                res = requesttypeTable.scan(**kwargs)
                requesttypeall += res['Items']

                if 'LastEvaluatedKey' in res:
                    lastEvaluatedKey = res['LastEvaluatedKey']
                else:
                    break
            entitlementattr = Attr('domainid').eq(domainid) & Attr('appid').eq(appid) 
            openingfilterattr = Attr('domainid').eq(domainid) & Attr('appid').eq(appid)
            if calendarid != "":
                entitlementattr &= Attr('calendarid').eq(calendarid)
                openingfilterattr &= Attr('calendarid').eq(calendarid)
            else:
                entitlementattr &= Attr('active').eq(True)
            entitlementlist = []
            lastEvaluatedKey = None
            while True:
                kwargs = {'FilterExpression': entitlementattr}
                if lastEvaluatedKey is not None:
                    kwargs |= {'ExclusiveStartKey': lastEvaluatedKey}

                res = entitlementTable.query(KeyConditionExpression = Key('orgid').eq(orgid),**kwargs)
                entitlementlist += res['Items']

                if 'LastEvaluatedKey' in res:
                    lastEvaluatedKey = res['LastEvaluatedKey']
                else:
                    break
            openinglist = []
            lastEvaluatedKey = None
            while True:
                kwargs = {"IndexName": "orgid-index",'FilterExpression': Attr('domainid').eq(domainid) & Attr('appid').eq(appid)}
                if lastEvaluatedKey is not None:
                    kwargs |= {'ExclusiveStartKey': lastEvaluatedKey}

                res = openingTable.query(KeyConditionExpression = Key('orgid').eq(orgid),**kwargs)
                openinglist += res['Items']

                if 'LastEvaluatedKey' in res:
                    lastEvaluatedKey = res['LastEvaluatedKey']
                else:
                    break
            calendarlist = []
            if calendarid != "":
                calendarres = calendarTable.get_item(
                    Key={
                        'orgid': orgid,
                        'calendarid': calendarid
                    }
                )
                if "Item" not in calendarres:
                    result = {
                        "list": [],
                        "returncode": "300"
                    }
                    return cb(200, result)
                calendarlist = [calendarres["Item"]]
                startdate = calendarres["Item"]['startdate']
                enddate = calendarres["Item"]['enddate']
            else:
                lastEvaluatedKey = None
                while True:
                    kwargs = {'FilterExpression': Attr('active').eq(True) & Attr('domainid').eq(domainid) & Attr('appid').eq(appid)}
                    if lastEvaluatedKey is not None:
                        kwargs |= {'ExclusiveStartKey': lastEvaluatedKey}

                    res = calendarTable.query(KeyConditionExpression = Key('orgid').eq(orgid),**kwargs)
                    calendarlist += res['Items']

                    if 'LastEvaluatedKey' in res:
                        lastEvaluatedKey = res['LastEvaluatedKey']
                    else:
                        break
            requestresponse = []
            lastEvaluatedKey = None
            while True:
                kwargs = {'FilterExpression': Attr('requesttype').eq("NCMLEIWHRNVIE") & (Attr('requeststatus').eq("002") |Attr('requeststatus').eq("004")) & Attr('domainid').eq(domainid) & Attr('appid').eq(appid) & ((Attr('startdate').gte(startdate) & Attr('startdate').lte(enddate)) | (Attr('enddate').gte(startdate) & Attr('enddate').lte(enddate)) | (Attr('startdate').lte(startdate) & Attr('enddate').gte(enddate)))}
                if lastEvaluatedKey is not None:
                    kwargs |= {'ExclusiveStartKey': lastEvaluatedKey}

                res = requestTable.query(KeyConditionExpression = Key('orgid').eq(orgid),**kwargs)
                requestresponse += res['Items']

                if 'LastEvaluatedKey' in res:
                    lastEvaluatedKey = res['LastEvaluatedKey']
                else:
                    break
            requestnode = {}
            for x in requestresponse: 
                if x['userid'] not in requestnode: 
                    requestnode[x['userid']]=[] 
                requestnode[x['userid']].append(x)
             # get member type list from table
            memberTypeData = []
            lastEvaluatedKey = None
            while True:
                kwargs = {}
                if lastEvaluatedKey is not None:
                    kwargs |= {'ExclusiveStartKey': lastEvaluatedKey}

                res = memberTypeTable.query(KeyConditionExpression=Key('orgid').eq(orgid),**kwargs)
                memberTypeData += res['Items']

                if 'LastEvaluatedKey' in res:
                    lastEvaluatedKey = res['LastEvaluatedKey']
                else:
                    break
            memberTypeNode={} 
            for mt in memberTypeData: 
                memberTypeNode[mt['primarykey']]=mt
            useridmappinglist = []
            lastEvaluatedKey = None
            while True:
                kwargs = {'FilterExpression':  Attr('domainid').eq(domainid) }
                if lastEvaluatedKey is not None:
                    kwargs |= {'ExclusiveStartKey': lastEvaluatedKey}

                res = UserIDMappingTable.query(KeyConditionExpression=Key('appid').eq(appid),**kwargs,ProjectionExpression="userid,parentid")
                useridmappinglist += res['Items']

                if 'LastEvaluatedKey' in res:
                    lastEvaluatedKey = res['LastEvaluatedKey']
                else:
                    break
            useridmappingnode={} 
            for mt in useridmappinglist: 
                useridmappingnode[mt['parentid']]=mt
            userlistObj = dict()
            userallrequest = []
            
            for i in range(len(userorglist)):
                if activestatus == "" or activestatus == "001":
                    valid = False
                    if ('transactiontype' not in userorglist[i] or userorglist[i]['transactiontype'] == "") or ('transactiontype' in userorglist[i] and userorglist[i]['transactiontype'] != "" and userorglist[i]['transactiontype'] in memberTypeNode and (memberTypeNode[userorglist[i]['transactiontype']]['status'] != "1" and memberTypeNode[userorglist[i]['transactiontype']]['status'] != "13" and memberTypeNode[userorglist[i]['transactiontype']]['status'] != "7")):
                        valid = True
                else:
                    valid = True
                    if ('transactiontype' not in userorglist[i] or userorglist[i]['transactiontype'] == "") or ('transactiontype' in userorglist[i] and userorglist[i]['transactiontype'] != "" and userorglist[i]['transactiontype'] in memberTypeNode and (memberTypeNode[userorglist[i]['transactiontype']]['status'] != "1" and memberTypeNode[userorglist[i]['transactiontype']]['status'] != "13" and memberTypeNode[userorglist[i]['transactiontype']]['status'] != "7")):
                        valid = False
                if valid == True:
                # if ('transactiontype' not in userorglist[i] or userorglist[i]['transactiontype'] == "") or ('transactiontype' in userorglist[i] and userorglist[i]['transactiontype'] != "" and userorglist[i]['transactiontype'] in memberTypeNode and (memberTypeNode[userorglist[i]['transactiontype']]['status'] != "1" and memberTypeNode[userorglist[i]['transactiontype']]['status'] != "13" and memberTypeNode[userorglist[i]['transactiontype']]['status'] != "7")):
                    userrequestlist = []
                    userrequestObj = dict()
                    userlistObj['userid'] = userorglist[i]['userid']
                    if userorglist[i]['userid'] in useridmappingnode:
                        userlistObj['userid'] = useridmappingnode[userorglist[i]['userid']]['userid']
                    # filteruserinfo = next(filter(lambda x: x['userid'] == userorglist[i]['userid'], userorglist),None)
                    # if filteruserinfo != None:
                    userlistObj['employeeid'] = userorglist[i]['employeeid']
                    userlistObj['username'] = userorglist[i]['username']
                    userlistObj['joineddate'] = userorglist[i]['joineddate']
                    userlistObj['department'] = userorglist[i]['department']
                    userlistObj['division'] = userorglist[i]['division']
                    userlistObj['typeid'] = userorglist[i]['typeid']
                    userlistObj['type'] = userorglist[i]['type']
                    userlistObj['post'] = userorglist[i]['post']
                    userlistObj['teamid'] = userorglist[i]['teamid']
                    userlistObj['costcenter'] = userorglist[i].get('costcenter',"") 
                    
                    # if len(filterrequestlist) > 0:
                    filteruserentitlement = next(filter(lambda x: x['userlist'].__contains__(userorglist[i]['userid']) and (len(calendarlist) > 0 and len(list(filter(lambda xx: xx['calendarid'] == x['calendarid'], calendarlist))) != 0), entitlementlist),None)
                    # return cb(200,filteruserentitlement)
                    entitleleavelist = []
                    openingrequestlist = [] 
                    if filteruserentitlement == None:
                        # if filteruserinfo != None:
                        
                        filtermembertype = next(filter(lambda x: x['membertype'].__contains__(userorglist[i]['type']) and (len(calendarlist) > 0 and len(list(filter(lambda xx: xx['calendarid'] == x['calendarid'], calendarlist))) != 0), entitlementlist),None)
                        if filtermembertype != None:
                            entitleleavelist = filtermembertype['requesttypelist']
                            filteropening = next(filter(lambda x: x['memberid'] == userorglist[i]['userid'] and x['calendarid'] == filtermembertype['calendarid'], openinglist),None)
                            if filteropening != None:
                                openingrequestlist = filteropening['requesttypelist']
                    else:
                        entitleleavelist = filteruserentitlement['requesttypelist']
                        filteropening = next(filter(lambda x: x['memberid'] == userorglist[i]['userid'] and x['calendarid'] == filteruserentitlement['calendarid'], openinglist),None)
                        
                        if filteropening != None:
                            openingrequestlist = filteropening['requesttypelist']
                    # return cb1(200,userorglist[i]['userid'])
                    # return cb(200,entitleleavelist)
                    requestresponse = None
                    if userorglist[i]['userid'] in requestnode:
                        requestresponse = requestnode[userorglist[i]['userid']]
                    # filterrequestlist = list(filter(lambda x: x['userid'] == userorglist[i]['userid'], requestresponse))
                    for e in range(len(entitleleavelist)):
                        filterrequesttype = next(filter(lambda x: x['requesttypeid'] == entitleleavelist[e]['requesttypeid'], requesttypeall),None)
                        if filterrequesttype != None:
                            requesttypename = filterrequesttype['requesttypename']
                        else:
                            requesttypename = ""
                        if len(userrequestlist) == 0:
                            userrequestObj['opening'] = ""
                            userrequestObj['broughtforward'] = 0
                            if len(openingrequestlist) > 0:
                                filteropeningrequest = next(filter(lambda x: x['requesttypeid'] == entitleleavelist[e]['requesttypeid'], openingrequestlist),None)
                                if filteropeningrequest != None:
                                    userrequestObj['opening'] = filteropeningrequest['opening']
                                    userrequestObj['broughtforward'] = str(filteropeningrequest['broughtforward'])
                            # filterrequestlist = list(filter(lambda x: x['userid'] == userorglist[i]['userid'], requestresponse))
                            userrequestObj['noofdays'] = entitleleavelist[e]['noofdays']
                            userrequestObj['requestsubtype'] = requesttypename
                            userrequestObj['requesttypeid'] = entitleleavelist[e]['requesttypeid']
                            userrequestObj['taken'] = 0
                            if requestresponse != None:
                                filterrequest = list(filter(lambda x: x['requestsubtype'] == entitleleavelist[e]['requesttypeid'], requestresponse))
                                if len(filterrequest) > 0:
                                    takencount = 0
                                    for f in range(len(filterrequest)):
                                        takencount += float(filterrequest[f]['duration'])
                                    userrequestObj['noofdays'] = entitleleavelist[e]['noofdays']
                                    userrequestObj['requestsubtype'] = requesttypename
                                    userrequestObj['requesttypeid'] = entitleleavelist[e]['requesttypeid']
                                    userrequestObj['taken'] = str(takencount)
                            # Calculate entitled leave count
                            entitled_count = float(userrequestObj['noofdays']) - float(userrequestObj['taken'])
                            userrequestObj['entitled_count'] = entitled_count
                            userrequestlist.append(userrequestObj.copy())
                        else:
                            userrequestObj['opening'] = ""
                            userrequestObj['broughtforward'] = 0
                            if len(openingrequestlist) > 0:
                                filteropeningrequest = next(filter(lambda x: x['requesttypeid'] == entitleleavelist[e]['requesttypeid'], openingrequestlist),None)
                                if filteropeningrequest != None:
                                    userrequestObj['opening'] = filteropeningrequest['opening']
                                    userrequestObj['broughtforward'] = str(filteropeningrequest['broughtforward'])
                            # filterrequestlist = list(filter(lambda x: x['userid'] == userorglist[i]['userid'], requestresponse))
                            userrequestObj['noofdays'] = entitleleavelist[e]['noofdays']
                            userrequestObj['requestsubtype'] = requesttypename
                            userrequestObj['requesttypeid'] = entitleleavelist[e]['requesttypeid']
                            userrequestObj['taken'] = 0
                            if requestresponse != None:
                                filterrequest = list(filter(lambda x: x['requestsubtype'] == entitleleavelist[e]['requesttypeid'], requestresponse))
                                if len(filterrequest) > 0:
                                    takencount = 0
                                    for f in range(len(filterrequest)):
                                        takencount += float(filterrequest[f]['duration'])
                                    userrequestObj['noofdays'] = entitleleavelist[e]['noofdays']
                                    userrequestObj['requestsubtype'] = requesttypename
                                    userrequestObj['requesttypeid'] = entitleleavelist[e]['requesttypeid']
                                    userrequestObj['taken'] = str(takencount)
                            # Calculate entitled leave count
                            entitled_count = float(userrequestObj['noofdays']) - float(userrequestObj['taken'])
                            userrequestObj['entitled_count'] = entitled_count
                            userrequestlist.append(userrequestObj.copy())
                    
                    userlistObj['requestlist'] = userrequestlist
                    userallrequest.append(userlistObj.copy())
            if len(userallrequest) > 0:
                userallrequest = sorted(userallrequest,key=lambda x: x["employeeid"])
            # return cb1(200,str(userallrequest))
            result = {
                "list": userallrequest,
                "returncode": "300"
            }
            return cb(200, result)
                
        except Exception as e:
            body = json.loads(event['body'])

            lineno = '{} on line {}'.format(
                e, sys.exc_info()[-1].tb_lineno)

            return common.AddServerErrorLog(functionname="getleavesummary", body=body, lineno=lineno)


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

def sortOrder(item):
    return item['sort']
