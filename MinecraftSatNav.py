#Minecraft Ordance Survey Sat Nav
#www.stuffaboutcode.com
#Martin O'Hanlon

import urllib, urllib2
import json
import mcpi.minecraft as minecraft
import mcpi.block as block
import mcpi.minecraftstuff as minecraftstuff
import time
import cmd
from math import floor
from OSConversion import *

#MapQuest API Key
MAPQUESTAPIKEY = "Fmjtd%7Cluurn9u825%2Crx%3Do5-9wzsg0"

#spawn location
SPAWNX = 17493
SPAWNY = 40
SPAWNZ = 47383

#minecraft ordinance survey sat nav
class MinecraftOSNav():

    def __init__(self):
        pass

    #calls the mapquest directions api
    def callDirectionsAPI(self, origin, destination):

        #the mapquest directions api url
        URL = "http://open.mapquestapi.com/directions/v2/route?key=" + MAPQUESTAPIKEY + "&ambiguities=ignore&"

        #build the url for this search, appending origin, destination and key
        directionsURL = URL + urllib.urlencode({"from": origin, "to": destination})

        #debug
        #print directionsURL

        #call the api and get the response
        req = urllib2.Request(directionsURL)
        res = urllib2.urlopen(req).read()
        
        #load the json
        result = json.loads(res)

        #debug save the json
        #with open("directionApiResponse.json", "w") as outfile:
        #    json.dump(result, outfile)

        #debug - print json
        #print json.dumps(result, sort_keys=True, indent=4, separators=(',', ': '))

        #return the result
        return result

    #def callDirectionsAPIStub(self, origin, destination):
    #    directionData=open("directionApiResponse.json")
    #
    #    res = json.load(directionData)
    #    
    #    return res

    #calls the mapquest geocoding api
    def callGeocodingAPI(self, location):

        #the mapquest directions api url
        URL = "http://open.mapquestapi.com/geocoding/v1/address?key=" + MAPQUESTAPIKEY + "&ambiguities=ignore&"

        #build the url for this search, appending origin, destination and key
        directionsURL = URL + urllib.urlencode({"location": location})

        #debug
        #print directionsURL

        #call the api and get the response
        req = urllib2.Request(directionsURL)
        res = urllib2.urlopen(req).read()
        
        #load the json
        result = json.loads(res)

        #debug save the json
        #with open("locationAPIResponse.json", "w") as outfile:
        #    json.dump(result, outfile)

        #debug - print json
        #print json.dumps(result, sort_keys=True, indent=4, separators=(',', ': '))

        #return the result
        return result


    #convert latitude and longitude to minecraft OSGB map X & Z coordinates
    #reverse engineered from http://www.ordnancesurvey.co.uk//innovate/developers/minecraft-coordinate-inset.html
    def convertLatLonToMCXZ(self, lat, lon):
        easting, northing = WGS84toOSGB36(lat, lon)
        x = floor(easting / 25)
        z = floor((1300000 - northing) / 25)
        return int(x),int(z)

    def convertMCXZToLatLon(self, x, z):
        easting = floor(x * 25)
        northing = floor(((z * 25) - 1300000) * -1)
        lat, lon = OSGB36toWGS84(easting, northing)
        return lat, lon

    # converts minecraft xyz to be reflective of spawn point
    #  as raspberry juice uses spawn point as 0,0,0
    def convertXYZToRaspiXYZ(self, x,y,z):        
        return int(x - SPAWNX), int(y - SPAWNY), int(z - SPAWNZ)

    # converts minecraft xyz to be reflective of spawn point
    #  as raspberry juice uses spawn point as 0,0,0
    def convertVec3ToRaspiVec3(self, vec3):
        return minecraft.Vec3(int(vec3.x - SPAWNX), int(vec3.y - SPAWNY), int(vec3.z - SPAWNZ))

    # converts xyz which comes from raspi to actual co-ordinates
    def convertRaspiXYZtoXYZ(self, x, y, z):
        return int(x + SPAWNX), int(y + SPAWNY), int(z + SPAWNZ)

    # converts xyz which comes from raspi to actual co-ordinates
    def convertRaspiVec3toVec3(self, vec3):
        return minecraft.Vec3(int(vec3.x + SPAWNX), int(vec3.y + SPAWNY), int(vec3.z + SPAWNZ))

    def convertDirectionsIntoMinecraftDirections(self, directions):
        #go through the directions and convert the steps to minecraft co-ordinates
        mcDirections = []

        #get the legs of the journey
        legs = directions["route"]["legs"]

        #loop through the legs
        for leg in legs:
            
            #loop through the steps and make a list of minecraft locations and directions
            for step in leg["maneuvers"]:
                x, z = self.convertLatLonToMCXZ(step["startPoint"]["lat"], step["startPoint"]["lng"])
                mcDirections.append([self.convertVec3ToRaspiVec3(minecraft.Vec3(x,100,z)), step["narrative"]])
                #debug print steps
                #print("Step  Lat:{}, Lon:{}".format(x,z))

        return mcDirections

    #create the route in Minecraft
    def followRoute(self, mc, mcDirections):
        #draw the route in minecraft
        
        #find the first direction
        direction1 = mcDirections[0]
        point1 = direction1[0]
        narrative = direction1[1]

        #move player to the first coord
        mc.player.setTilePos(point1.x, mc.getHeight(point1.x, point1.z), point1.z)
        
        #loop through all the points
        for direction2 in mcDirections[1:]:

            #put the directions on the screen
            mc.postToChat(narrative.encode('ascii', 'ignore'))

            #draw the line between1 the points
            point2 = direction2[0]
            self.drawLineLevelWithGround(mc,
                                          point1.x, point1.y, point1.z,
                                          point2.x, point2.y, point2.z,
                                          3,
                                          block.WOOL.id, 15)

            #wait till the player has reached the point
            pos = mc.player.getTilePos()
            while(pos.x != point2.x and pos.z != point2.z):
                pos = mc.player.getTilePos()
                time.sleep(0.1)

            #move onto the next point
            direction1 = direction2
            point1 = direction1[0]
            narrative = direction1[1]

    #clear the route in minecraft
    def clearRoute(self, mc, mcDirections):

        #find the first direction
        direction1 = mcDirections[0]
        point1 = direction1[0]
        narrative = direction1[1]

        #loop through all the points
        for direction2 in mcDirections[1:]:

            #draw the line between the points
            point2 = direction2[0]
            self.drawLineLevelWithGround(mc,
                                         point1.x, point1.y, point1.z,
                                         point2.x, point2.y, point2.z,
                                         -1,
                                         block.AIR.id)

            #move onto the next point
            direction1 = direction2
            point1 = direction1[0]
            narrative = direction1[1]

    #draw a line between 2 points level with the ground
    def drawLineLevelWithGround(self, mc, x1, y1, z1, x2, y2, z2, heightAboveGround, blockType, blockData = 0):
        #create minecraft drawing object, used to create the lines
        mcDrawing = minecraftstuff.MinecraftDrawing(mc)

        #get the line
        blocksInLine = mcDrawing.getLine(x1,y1,z1,x2,y2,z2)

        #loop through blocks in line
        for blockInLine in blocksInLine[1:]:
            #get height of land 
            y = mc.getHeight(blockInLine.x, blockInLine.z) + heightAboveGround
            #create the block
            mc.setBlock(blockInLine.x, y, blockInLine.z, blockType, blockData)

    #navigate from a location to a destination
    def navigateFrom(self, origin, destination):

        print("Getting Directions Courtesy of MapQuest")

        #get the directions from mapquest api
        #directions = self.callDirectionsAPIStub(origin, destination)
        directions = self.callDirectionsAPI(origin, destination)

        #was the call a success?
        if directions["info"]["statuscode"] == 0:
            
            #create connection to minecraft
            mc = minecraft.Minecraft.create()

            #convert the directions into mc directions
            mcDirections = self.convertDirectionsIntoMinecraftDirections(directions)
            mc.postToChat("Route calculated between " + origin + " and " + destination)

            #follow the route
            self.followRoute(mc, mcDirections)

            #when finished - clear the route
            mc.postToChat("You have reached your destination.  Clearing route")
            self.clearRoute(mc, mcDirections)
            mc.postToChat("Route cleared")
            
        #the call to mapquest api failed
        else:
            print("Failed to get directions - status = {}, messages = '{}'".format(directions["info"]["statuscode"], directions["info"]["messages"][0].encode('ascii', 'ignore')))

    #navigate from the players current location to a destination
    def navigate(self, destination):

        #create connection to minecraft
        mc = minecraft.Minecraft.create()

        #get the players position
        pos = mc.player.getTilePos()

        #get the players lat and lon
        actualPos = self.convertRaspiVec3toVec3(pos)
        lat, lon = self.convertMCXZToLatLon(actualPos.x, actualPos.z)
        origin = str(lat) + "," + str(lon)

        #get directions
        directions = self.callDirectionsAPI(origin, destination)

        #was the call a success?
        if directions["info"]["statuscode"] == 0:
            #convert the directions into mc directions
            mcDirections = self.convertDirectionsIntoMinecraftDirections(directions)
            mc.postToChat("Route calculated between your position and " + destination)

            #follow the route
            self.followRoute(mc, mcDirections)

            #when finished - clear the route
            mc.postToChat("You have reached your destination.  Clearing route")
            self.clearRoute(mc, mcDirections)
            mc.postToChat("Route cleared")

        #the call to mapquest api failed
        else:
            print("Failed to get directions - status = {}, messages = '{}'".format(directions["info"]["statuscode"], directions["info"]["messages"][0].encode('ascii', 'ignore')))

    #teleport the player to a location
    def teleport(self, location):
        #call the mapquest api to find the location
        locations = self.callGeocodingAPI(location)

        #was the call a success?
        if locations["info"]["statuscode"] == 0:
            #was a location found?
            if len(locations["results"][0]["locations"]) > 0:
                #get lat and lon for first location found
                lat = locations["results"][0]["locations"][0]["latLng"]["lat"]
                lon = locations["results"][0]["locations"][0]["latLng"]["lng"]
                #get minecraft x,z
                x,z = self.convertLatLonToMCXZ(lat,lon)
                #convert this to be reflect of spawn
                x,y,z = self.convertXYZToRaspiXYZ(x,0,z)
                #create connection to minecraft
                mc = minecraft.Minecraft.create()
                #find the height of the world
                y = mc.getHeight(x,z)
                #move player
                mc.player.setTilePos(x,y,z)
                mc.postToChat("Teleported to " + location)
            else:
                print("No location could be found for '" + location + "'")
        else:
            print("Failed to get location - status = {}, messages = '{}'".format(directions["info"]["statuscode"], directions["info"]["messages"][0].encode('ascii', 'ignore')))


# Class to manage the command line interface
class NavigationCommands(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "OS Map Nav >> "
        self.intro  = "Minecraft OS Sat-Nav - www.stuffaboutcode.com"
        #create navigation object
        self.nav = MinecraftOSNav()

    def do_exit(self, args):
        "Exit navigation [exit]"
        return -1

    def do_navigate(self, destination):
        "Navigate to a destination [navigate <destination>]"
        self.nav.navigate(destination)

    def do_navigateFrom(self, args):
        "Navigate from a start position to a destination [navigate <start>,<destination>]"

        #split the arguments
        args = args.split(",")

        if len(args) == 2:
            self.nav.navigateFrom(args[0], args[1])
        else:
            print("Error: expected 2 arguments")

    def do_teleport(self, location):
        "Teleport to a location [teleport <location>]"
        self.nav.teleport(location)
        
    def do_EOF(self, line):
        return True

#Main program
if __name__ == "__main__":
    #start command line
    NavigationCommands().cmdloop()
    
