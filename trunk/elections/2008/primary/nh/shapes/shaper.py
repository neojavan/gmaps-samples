#!/usr/bin/env python

iconBaseUrl = 'http://gmaps-samples.googlecode.com/svn/trunk/elections/2008/images/icons/'

import private
import reader
import elementtree.ElementTree as ET
import simplejson as sj
import random

#def str( text ):
#	strings = {
#		'county': 'town',
#		'counties': 'towns'
#	}
#	return strings[text] or text

def randomColor():
	return hh() + hh() + hh()

def hh():
	return '%02X' %( random.random() *256 )

def makeKML( earth=False ):
	xmlRoot = ET.parse( 'cs33_d00_shp' + ['','-94'][earth] + '/cs33_d00.gpx' )
	
	counties = {}
	
	for xmlCounty in xmlRoot.getiterator('rte'):
		points = []
		for xmlPoint in xmlCounty.getiterator('rtept'):
			points.append( [ xmlPoint.attrib['lat'].strip(), xmlPoint.attrib['lon'].strip() ] )
		name = xmlCounty.findtext('name').strip()
		number = xmlCounty.findtext('number').strip()
		# Correct error in census data for Wentworth's Location
		if( name == "Wentworth" and number == '9' ):
			name = "Wentworth's Location"
		county = {
			'name': name,
			'points': points,
			'centroid': polyCentroid( points )
		}
		counties[name] = county
	state = {}
	reader.readVotes( state, counties )
	
	writeKML( earth, counties, 'democrat' )
	writeKML( earth, counties, 'republican' )

def writeKML( earth, counties, party ):
	print 'Writing ' + party
	nPoints = 0
	kml = ET.Element( 'kml', { 'xmlns':'http://earth.google.com/kml/2.0' } )
	kmlDocument = ET.SubElement( kml, 'Document' )
	kmlFolder = ET.SubElement( kmlDocument, 'Folder' )
	kmlFolderName = ET.SubElement( kmlFolder, 'name' )
	kmlFolderName.text = 'New Hampshire Towns'
	for name, county in counties.iteritems():
		kmlPlacemark = ET.SubElement( kmlFolder, 'Placemark' )
		kmlPlaceName = ET.SubElement( kmlPlacemark, 'name' )
		kmlPlaceName.text = name
		kmlMultiGeometry = ET.SubElement( kmlPlacemark, 'MultiGeometry' )
		if earth:
			kmlPoint = ET.SubElement( kmlMultiGeometry, 'Point' )
			kmlPointCoordinates = ET.SubElement( kmlPoint, 'coordinates' )
			kmlPointCoordinates.text = coord( county['centroid'] )
		kmlPolygon = ET.SubElement( kmlMultiGeometry, 'Polygon' )
		kmlOuterBoundaryIs = ET.SubElement( kmlPolygon, 'outerBoundaryIs' )
		kmlLinearRing = ET.SubElement( kmlOuterBoundaryIs, 'LinearRing' )
		kmlCoordinates = ET.SubElement( kmlLinearRing, 'coordinates' )
		kmlCoordinates.text = ' '.join([ coord(point) for point in county['points'] ])
		kmlStyle = ET.SubElement( kmlPlacemark, 'Style' )
		if earth:
			kmlIconStyle = ET.SubElement( kmlStyle, 'IconStyle' )
			kmlIcon = ET.SubElement( kmlIconStyle, 'Icon' )
			kmlIconHref = ET.SubElement( kmlIcon, 'href' )
			leader = getLeader(county,party) or { 'name': 'generic' }
			kmlIconHref.text = iconBaseUrl + leader['name'] + '-border.png'
		kmlLineStyle = ET.SubElement( kmlStyle, 'LineStyle' )
		kmlLineStyleColor = ET.SubElement( kmlLineStyle, 'color' )
		kmlLineStyleColor.text = '40000000'
		kmlLineStyleWidth = ET.SubElement( kmlLineStyle, 'width' )
		kmlLineStyleWidth.text = '1'
		kmlPolyStyle = ET.SubElement( kmlStyle, 'PolyStyle' )
		kmlPolyStyleColor = ET.SubElement( kmlPolyStyle, 'color' )
		kmlPolyStyleColor.text = getColor( county, party )
	
	kmlTree = ET.ElementTree( kml )
	kmlfile = open( private.targetKML + party + '.kml', 'w' )
	kmlfile.write( '<?xml version="1.0" encoding="utf-8" ?>\n' )
	kmlTree.write( kmlfile )
	kmlfile.close()
	
	ctyNames = []
	for name in counties:
		ctyNames.append( name )
	ctyNames.sort()
	#for name in ctyNames:
	#	print name
	
	ctys = []
	for name in ctyNames:
		county = counties[name]
		pts = []
		#for point in county['points']:
		#	pts.append( '[%s,%s]' %( point[0], point[1] ) )
		#ctys.append( '{name:"%s",centroid:[%.8f,%.8f],points:[%s]}' %(
		#	county['name'],
		#	','.join(pts)
		#) )
		pts = []
		#lats = lons = 0
		minLat = minLon = 360
		maxLat = maxLon = -360
		centroid = county['centroid']
		points = county['points']
		for point in points:
			nPoints += 1
			pts.append( '[%s,%s]' %( point[0], point[1] ) )
		ctys.append( '{name:"%s",centroid:[%.8f,%.8f],points:[%s]}' %(
			reader.fixCountyName( name ),
			centroid[0], centroid[1],
			','.join(pts)
		) )
	
	print '%d points in %d places' %( nPoints, len(ctys) )
	return '[%s]' % ','.join(ctys)

def coord( point ):
	return str(point[1]) + ',' + str(point[0]) + ',0'

def getColor( county, party ):
	leader = getLeader( county, party )
	if not leader:
		return '00000000';
	else:
		return 'C0' + bgr( leader['color'] )

def getLeader( county, party ):
	tally = county.get(party)
	if tally == None  or  len(tally) == 0:
		return None
	return reader.candidates['byname'][party][ tally[0]['name'] ]

def bgr( rgb ):
	return rgb[5:7] + rgb[3:5] + rgb[1:3]

# Port of ANSI C code from the article
# "Centroid of a Polygon"
# by Gerard Bashein and Paul R. Detmer,
# (gb@locke.hs.washington.edu, pdetmer@u.washington.edu)
# in "Graphics Gems IV", Academic Press, 1994
# http://tog.acm.org/GraphicsGems/gemsiv/centroid.c
def polyCentroid( points ):
	def fix( pt ): return [ float(pt[0]), float(pt[1]) ]
	n = len(points)
	atmp = xtmp = ytmp = 0
	if n < 3: return []
	pI = fix( points[n-1] )
	for j in xrange( 0, n ):
		pJ = fix( points[j] )
		ai = pI[0] * pJ[1] - pJ[0] * pI[1]
		atmp += ai
		xtmp += ( pJ[0] + pI[0] ) * ai
		ytmp += ( pJ[1] + pI[1] ) * ai;
		pI = pJ
	area = atmp / 2;
	if atmp == 0: return []
	return [ xtmp / (3 * atmp), ytmp / (3 * atmp) ]

def write( name, text ):
	f = open( name, 'w' )
	f.write( text )
	f.close()

def main():
	print 'Starting...'
	makeKML( True )
	if False:
		write( '../data.js', '''
Data = {
//	counties: %s
};
''' %( makeKML() ) )
	print 'Done!'

if __name__ == "__main__":
    main()
