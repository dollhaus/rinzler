import discord
import DiscordUtils
from datetime import datetime, timedelta
from mysql.connector import connect, Error
from dateutil.relativedelta import relativedelta
from dateutil import parser


intents = discord.Intents.all()
client = discord.Client(intents=intents)


isCap = False
mysqlError = ""
unbanDate = ""
time = ""
writtenBanTime = ""
timeDigit = 0
memberToUnban = ""
responsestr = ""


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    global sqlstring
    global guild
    global mysqlError
    global unbanDate
    global time
    global writtenBanTime
    global timeDigit
    global isCap
    global memberToUnban
    global responsestr

    guild = client.get_guild(<guild>)
    
    memberToUnban = testForUnbannedMembers()
    if (memberToUnban > 2):
        channel = client.get_channel(<channel>)
        await send_message(channel, '<@<role>>s, it\'s time to unban <@' + memberToUnban + '>. Bots can\'t do this automatically.') #They can, but I want people to be alert when this takes place to watch for repercussions
        
    
    if message.author == client.user:
        return
    
    if (authorIsMod(message.author.id) and message.content.lower() == ('sic \'em rinzi')):
        await message.channel.send('grr')
    
    if (message.channel.name == 'onboarding'):
        onbStr = "".join(filter(str.isalpha, message.content.lower()))
        print(onbStr)
        if (onbStr == ('dontbemean')):
            user = await guild.fetch_member(message.author.id)
            onboarded = discord.utils.get(guild.roles, id=1030858857603403796)
            notonboarded = discord.utils.get(guild.roles, id=1030867790040678482)
            newuser = discord.utils.get(guild.roles, id=816403740634382396)
            await user.add_roles(onboarded)
            await user.add_roles(newuser)
            await user.remove_roles(notonboarded)
        await message.delete()        
        returnn
        
    if message.channel.name != 'mod-chat':
        return
    
	
	
    #usage: !ban <@user>/<length of ban>/<reason>/<message to send to user>
    if (authorIsMod(message.author.id) and message.content.startswith('!ban')):
        banVars = message.content[5:].split('/')
        if (len(banVars) < 4):
            await message.channel.send('Usage: `!ban @user/<length of ban>/<reason>/<message to send to user>`\nFor time delineation, use `0` for  a permanent ban. Other deltas include:\n`m` - minutes\n`h` - hours\n`d` - days\n`w` - weeks\n`M` - months \nThe message will automatically include "You have been banned from The Grid for *time*/permanently", you do not need to include this.')
            return
        banSubject = banVars[0]
        banTime = banVars[1]
        banReason = banVars[2]
        banMessage = banVars[3]
        local_unbanDate = ""
        if banTime == "0":
            interdate = (datetime.now() + timedelta(years=100))#Dirty way of doing it, tbh, but a date of today or in the past would cycle the unban ping
            local_unbanDate = str(interdate)
        else:
            unbanParse = timeCalc(banTime)
            writtenBanTime = unbanParse.split('|')[0]
            local_unbanDate = unbanParse.split('|')[1]
        if "@" in banSubject:
            namedUser = banSubject
            remove = "<@>"
            for char in remove:
                namedUser = namedUser.replace(char, "")
            bannedUser = await guild.fetch_member(namedUser)
            if addBanToDB(bannedUser.id, local_unbanDate, message.author.id, banReason, banMessage):
                if (banTime == "0"):
                    await message.channel.send('Banned <@' + str(bannedUser.id) + '> permanently for reason:' + banReason)
                    await bannedUser.send('You have been banned from The Grid permanently. The following message was included: \n\n' + banMessage)
                else:
                    await message.channel.send('Banned <@' + str(bannedUser.id) + '> for ' + writtenBanTime + ' for reason ' + banReason)
                    await bannedUser.send('You have been excluded from The Grid for' + writtenBanTime +'. The following message was included: \n\n' + banMessage)
                await bannedUser.ban(reason=banReason)
                return
            else:
                await message.channel.send('I had trouble connecting to the database. This ban could not be performed, please contact delinquent for help. \n Error: ' + mysqlError)
                mysqlError = ""
                return
        else:
            await message.channel.send('Usage: `!ban @user/<length of ban>/<reason>/<message to send to user>`\nFor time delineation, use `0` for  a permanent ban. Other deltas include:\n`m` - minutes\n`h` - hours\n`d` - days\n`w` - weeks\n`M` - months \nThe message will automatically include "You have been banned from The Grid for *time*/permanently", you do not need to include this.')

    if (authorIsMod(message.author.id) and message.content.startswith('!promote')):
        if "@" in message.content[9:]:
            namedUser = message.content[9:]
            remove = '<@>'
            for char in remove:
                namedUser = namedUser.replace(char, "")
            userToPromote = await guild.fetch_member(namedUser)
            if (promoteToModerator(userToPromote.id, message.author.id)):
                modRole = discord.utils.get(guild.roles, id=708367592049475705)
                await userToPromote.add_roles(modRole)
                await message.channel.send('Promoted <@' + str(userToPromote.id) + '>!')
                return
            else:
                if len(mysqlError) > 2:
                    await message.channel.send('I had trouble connecting to the database. This promotion could not be performed, please contact delinquent for help. \n Error: ' + mysqlError)
                    return
        else:
            await message.channel.send('`Usage: !promote @user`')
            return

    if (authorIsMod(message.author.id) and message.content.startswith('!demote')):
        if "@" in message.content[9:]:
            namedUser = message.content[9:]
            remove = '@<>'
            for char in remove:
                namedUser = namedUser.replace(char, "")
            userToDemote = await guild.fetch_member(namedUser)
            if (demoteFromModerator(userToDemote.id)):
                modRole = discord.utils.get(guild.roles, id=708367592049475705)
                await userToDemote.remove_roles(modRole)
                await message.channel.send('Demoted <@' + str(userToDemote.id) + '>!')
                return
            else:
                if len(mysqlError) > 2:
                    await message.channel.send('I had trouble connecting to the database. This demotion could not be performed, please contact delinquent for help. \n Error: ' + mysqlError)
                    return
        else:
            await message.channel.send('`Usage: !demote @user`')
            return

############################
###      responses       ###
############################
    
    if message.content.startswith('you up rinzler') and authorIsMod(message.author.id):
        await message.channel.send('grrr')

    if message.content.startswith('!testtime'):
        await message.channel.send(str(datetime.now()) + '\n' + timeCalc(message.content[10:])) # for testing the time deltas. Dunno why but they were being a pain

    
############################
###    fixed methods    ####
############################

def authorIsMod(authorid):
    isMod = bool()
    try:
        with connect(
            host="",
            user="",
            password="",
            database="",
        ) as connection:
            cursor = connection.cursor()
            cursor.execute("select * from <table> where userid = '" + str(authorid) + "'")
            result = cursor.fetchall()
            #if len(result) > 0:
            #   isMod = true
            #    return isMod
            #return false
            return bool(len(result) >= 0)
    except Error as e:
        mysqlError = e
        isMod = "false"
        return isMod
    #finally:
    #    if connection.is_connected():
    #        cursor.close()
    #        connection.close()
    

def addBanToDB(id, lengthOfBan, bannedby, reason, pmtouser):
    banSuccessful = bool()
    try:
        with connect(
            host="",
            user="",
            password="",
            database="",
        ) as connection:
            cursor = connection.cursor()
            insertBan = """
            INSERT INTO <table>
            (userid, lengthofban, bannedby, reason, pmtouser)
            VALUES ( %s, %s, %s, %s, %s )
            """
            value = (str(id), lengthOfBan, str(bannedby), reason, pmtouser)
            cursor.execute(insertBan, value)
            connection.commit()
            banSuccessful = True
            return banSuccessful
    except Error as e:
        mysqlError = e
        return banSuccessful
    #finally:
    #    if connection.is_connected():
    #        cursor.close()                       #I structured this wrong. tbh the connection should never really hang, but if it does any exceptions are caught anyway in the bool that calls this method
    #        connection.close()
    

def promoteToModerator(idToPromote, promotedBy):
    promotionSuccessful = bool()
    try:
        with connect(
            host="",
            user="",
            password="",
            database="",
        ) as connection:
            cursor = connection.cursor()
            insertMod = """
            INSERT INTO <table>
            (userid, promotedby)
            VALUES ( %s, %s )
            """
            value = (str(idToPromote), str(promotedBy))
            cursor.execute(insertMod, value)
            connection.commit()
            promotionSuccessful = True
            return promotionSuccessful
    except Error as e:
        mysqlError = e
        promotionSuccessful = False
        return promotionSuccessful

def demoteFromModerator(idToDemote):
    demotionSuccessful = bool()
    try:
        with connect(
            host="",
            user="",
            password="",
            database="",
        ) as connection:
            cursor = connection.cursor()
            removeMod = """
            DELETE FROM <table>
            WHERE userid = %s
            """
            value = (str(idToDemote))
            cursor.execute(removeMod, value)
            connection.commit()
            demotionSuccessful = True
            return demotionSuccessful
    except Error as e:
        mysqlError = e
        demotionSuccessful = False
        return demotionSuccessful

def testForUnbannedMembers():
    bannedMembersQuery = "SELECT * FROM bannedusers LIMIT 10"
    bannedUserID = ""
    UnbanDateString = ""    
    try:
        with connect(
            host="",
            user="",
            password="",
            database="",
        ) as connection:
            cursor = connection.cursor()
            cursor.execute(bannedMembersQuery)
            bannedMembers = cursor.fetchall()
            for row in <table>:
                bannedUserID = row[0]
                now = datetime.now()
                UnbanDateString = row[1]
                local_UnbanDate = parser.parse(UnbanDateString)
                if local_UnbanDate < now:
                    removeBanFromDB(bannedUserID)
                    memberToUnban = bannedUserID
                    return True
            return False
    except Error as e:
        mysqlError = e
        return False

def removeBanFromDB(bannedUserID):
    try:
        with connect(
            host="",
            user="",
            password="",
            database="",
        ) as connection:
            cursor = connection.cursor()
            removeBan = """
            DELETE FROM <table>
            WHERE userid = %s
            """
            value = (str(bannedUserID))
            cursor.execute(removeBan, value)
            connection.commit()
    except Error as e:
        mysqlError = e
        return
    
def timeCalc(banTime):
    isCap = False
    for a in banTime:
        if a.upper():
            isCap = True
        break
    time=""
    delineator=""
    for b in banTime:
        if (b.isdigit()):
            time+=str(b)
        else:
            delineator+=b
    timeDigit = int(time)
    print(timeDigit + 30)
    return doTimeAdditions(timeDigit, delineator, isCap)

def doTimeAdditions(t, d, isCap):
    if (d =='m' or d =='M'):
        return addMonthsOrMinutes(t, isCap)
    if d=='d':
        return addDays(t)
    if d=='w':
        return addWeeks(t)
    if d=='h':
        return addHours(t)

def toDigit(timestr):
    return int(timestr)

def addMonthsOrMinutes(t, isCap):
    if isCap==True:
        interdate = datetime.now() + relativedelta(months=t)
        unbanDate = str(interdate)
        writtenBanTime = (str(t) + " months")
        return writtenBanTime + "|" + unbanDate
    else:
        interdate = datetime.now() + timedelta(minutes=t)
        unbanDate = str(interdate)
        writtenBanTime = (str(t) + " minutes")
        return writtenBanTime + "|" + unbanDate

def addDays(t):
    interdate = datetime.now() + timedelta(days=t)
    unbanDate = str(interdate)
    writtenBanTime = (str(t) + " days")
    return writtenBanTime + "|" + unbanDate

def addWeeks(t):
    interdate = datetime.now() + timedelta(weeks=t)
    unbanDate = str(interdate)
    writtenBanTime = (str(t) + " weeks")
    return writtenBanTime + "|" + unbanDate

def addHours(t):
    interdate = datetime.now() + timedelta(hours=t)
    unbanDate = str(interdate)
    writtenBanTime = (str(t) + " hours")
    return writtenBanTime + "|" + unbanDate



client.run('TOKEN')
