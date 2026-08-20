"""
Reference pools used by the mock data generator.

Everything here is synthetic filler: name lists, street words, and real
US city/state/ZIP combinations so that addresses look plausible and so
that state/ZIP mismatches can be planted deliberately.
"""

FIRST_NAMES_F = """Mary Patricia Jennifer Linda Elizabeth Barbara Susan Jessica Sarah Karen Nancy Lisa
Betty Margaret Sandra Ashley Kimberly Emily Donna Michelle Carol Amanda Dorothy Melissa Deborah Stephanie
Rebecca Sharon Laura Cynthia Kathleen Amy Angela Shirley Anna Brenda Pamela Nicole Ruth Katherine Samantha
Christine Emma Catherine Debra Virginia Rachel Carolyn Janet Maria Heather Diane Julie Joyce Victoria Kelly
Christina Joan Evelyn Lauren Judith Olivia Frances Martha Cheryl Megan Andrea Hannah Jacqueline Ann Gloria
Jean Kathryn Alice Teresa Sara Janice Doris Madison Julia Grace Judy Abigail Marie Denise Beverly Amber
Theresa Marilyn Danielle Diana Brittany Natalie Sophia Rose Isabella Alexis Kayla Erica Monica Tracy Wanda""".split()

FIRST_NAMES_M = """James Robert John Michael David William Richard Joseph Thomas Christopher Charles Daniel
Matthew Anthony Mark Donald Steven Andrew Paul Joshua Kenneth Kevin Brian George Timothy Ronald Jason Edward
Jeffrey Ryan Jacob Gary Nicholas Eric Jonathan Stephen Larry Justin Scott Brandon Benjamin Samuel Gregory
Alexander Patrick Frank Raymond Jack Dennis Jerry Tyler Aaron Jose Adam Nathan Henry Zachary Douglas Peter
Kyle Noah Ethan Jeremy Walter Christian Keith Roger Terry Austin Sean Gerald Carl Harold Dylan Arthur Lawrence
Jordan Jesse Bryan Billy Bruce Gabriel Joe Logan Alan Juan Albert Willie Elijah Wayne Randy Vincent Mason
Roy Ralph Bobby Russell Bradley Philip Eugene Marcus Curtis Travis Derrick Andre Clifford Leon""".split()

LAST_NAMES = """Smith Johnson Williams Brown Jones Garcia Miller Davis Rodriguez Martinez Hernandez Lopez
Gonzalez Wilson Anderson Thomas Taylor Moore Jackson Martin Lee Perez Thompson White Harris Sanchez Clark
Ramirez Lewis Robinson Walker Young Allen King Wright Scott Torres Nguyen Hill Flores Green Adams Nelson
Baker Hall Rivera Campbell Mitchell Carter Roberts Gomez Phillips Evans Turner Diaz Parker Cruz Edwards
Collins Reyes Stewart Morris Morales Murphy Cook Rogers Gutierrez Ortiz Morgan Cooper Peterson Bailey Reed
Kelly Howard Ramos Kim Cox Ward Richardson Watson Brooks Chavez Wood James Bennett Gray Mendoza Ruiz Hughes
Price Alvarez Castillo Sanders Patel Myers Long Ross Foster Jimenez Powell Jenkins Perry Russell Sullivan
Bell Coleman Butler Henderson Barnes Gonzales Fisher Vasquez Simmons Romero Jordan Patterson Alexander
Hamilton Graham Reynolds Griffin Wallace Moreno West Cole Hayes Bryant Herrera Gibson Ellis Tran Medina
Aguilar Stevens Murray Ford Castro Marshall Owens Harrison Fernandez McDonald Woods Washington Kennedy
Wells Vargas Henry Chen Freeman Webb Tucker Guzman Burns Crawford Olson Simpson Porter Hunter Gordon Mendez
Silva Shaw Snyder Mason Dixon Hunt Hicks Holmes Palmer Wagner Black Robertson Boyd Rose Stone Salazar Fox
Warren Mills Meyer Rice Schmidt Garza Daniels Ferguson Nichols Stephens Soto Weaver Ryan Gardner Payne
Grant Dunn Kelley Spencer Hawkins Arnold Pierce Vazquez Hansen Peters Santos Hart Bradley Knight Elliott
Cunningham Duncan Armstrong Hudson Carroll Lane Riley Andrews Harper Fowler Burke Larson Carlson Austin
Lawson Reid Chapman Barrett Weber Walsh Schultz Bowman Barker Sutton Ingram Nunez Pena Rios Delgado""".split()

MIDDLE_INITIALS = list("ABCDEFGHJKLMNPRSTW")
SUFFIXES = ["JR", "SR", "II", "III", "IV"]

STREET_NAMES = """Main Oak Maple Cedar Elm Washington Lake Hill Walnut Spring Ridge Pine Sunset Lincoln
Willow Church Highland Jefferson Chestnut Franklin Park Prospect Center Adams River Meadow Jackson Dogwood
Madison College Cherry Poplar Hickory Woodland Fairview Broad Union Second Third Fourth Fifth Sixth Seventh
Laurel Magnolia Sycamore Birch Aspen Juniper Vine Grove Summit Valley Forest Bay Harbor Canyon Mesa Prairie
Buckeye Sherwood Wilson Monroe Tyler Harrison Grant Kennedy Roosevelt Carver Bridge Mill Depot Market
State Court Water Front Pearl Pleasant School Academy Liberty Freedom Victory Progress Industrial Commerce
Airport Orchard Garden Rose Tulip Holly Ivy Fern Clover Bluebird Cardinal Falcon Eagle Heron Dover Salem
Concord Auburn Clayton Ashford Bellevue Glenwood Rockwood Stonebridge Foxglove Wintergreen Braewood""".split()

STREET_TYPES = ["St", "Ave", "Rd", "Dr", "Ln", "Ct", "Blvd", "Way", "Pl", "Ter", "Cir", "Pkwy"]
UNIT_TYPES = ["Apt", "Unit", "Ste", "#", "Bldg", "Trlr"]

# (city, state, zip5) -- real US city/state/ZIP combinations.
CITIES = [
    ("Boston", "MA", "02108"), ("Worcester", "MA", "01602"), ("Springfield", "MA", "01103"),
    ("Providence", "RI", "02903"), ("Warwick", "RI", "02886"), ("Hartford", "CT", "06103"),
    ("New Haven", "CT", "06511"), ("Bridgeport", "CT", "06604"), ("Manchester", "NH", "03101"),
    ("Nashua", "NH", "03060"), ("Portland", "ME", "04101"), ("Bangor", "ME", "04401"),
    ("Burlington", "VT", "05401"), ("Newark", "NJ", "07102"), ("Jersey City", "NJ", "07302"),
    ("Trenton", "NJ", "08608"), ("Camden", "NJ", "08103"), ("Paterson", "NJ", "07501"),
    ("New York", "NY", "10001"), ("Brooklyn", "NY", "11201"), ("Bronx", "NY", "10451"),
    ("Buffalo", "NY", "14202"), ("Rochester", "NY", "14604"), ("Syracuse", "NY", "13202"),
    ("Albany", "NY", "12207"), ("Yonkers", "NY", "10701"), ("Philadelphia", "PA", "19104"),
    ("Pittsburgh", "PA", "15213"), ("Allentown", "PA", "18101"), ("Erie", "PA", "16501"),
    ("Scranton", "PA", "18503"), ("Wilmington", "DE", "19801"), ("Baltimore", "MD", "21201"),
    ("Silver Spring", "MD", "20901"), ("Washington", "DC", "20001"), ("Richmond", "VA", "23219"),
    ("Virginia Beach", "VA", "23451"), ("Norfolk", "VA", "23510"), ("Arlington", "VA", "22201"),
    ("Charleston", "WV", "25301"), ("Charlotte", "NC", "28202"), ("Raleigh", "NC", "27601"),
    ("Greensboro", "NC", "27401"), ("Durham", "NC", "27701"), ("Columbia", "SC", "29201"),
    ("Charleston", "SC", "29403"), ("Greenville", "SC", "29601"), ("Atlanta", "GA", "30303"),
    ("Savannah", "GA", "31401"), ("Augusta", "GA", "30901"), ("Macon", "GA", "31201"),
    ("Jacksonville", "FL", "32202"), ("Miami", "FL", "33125"), ("Tampa", "FL", "33602"),
    ("Orlando", "FL", "32801"), ("St Petersburg", "FL", "33701"), ("Hialeah", "FL", "33010"),
    ("Fort Lauderdale", "FL", "33301"), ("Tallahassee", "FL", "32301"), ("Birmingham", "AL", "35203"),
    ("Montgomery", "AL", "36104"), ("Mobile", "AL", "36602"), ("Jackson", "MS", "39201"),
    ("Nashville", "TN", "37203"), ("Memphis", "TN", "38103"), ("Knoxville", "TN", "37902"),
    ("Chattanooga", "TN", "37402"), ("Louisville", "KY", "40202"), ("Lexington", "KY", "40507"),
    ("Columbus", "OH", "43215"), ("Cleveland", "OH", "44113"), ("Cincinnati", "OH", "45202"),
    ("Toledo", "OH", "43604"), ("Akron", "OH", "44308"), ("Dayton", "OH", "45402"),
    ("Detroit", "MI", "48226"), ("Grand Rapids", "MI", "49503"), ("Lansing", "MI", "48933"),
    ("Flint", "MI", "48502"), ("Indianapolis", "IN", "46204"), ("Fort Wayne", "IN", "46802"),
    ("Evansville", "IN", "47708"), ("Chicago", "IL", "60614"), ("Aurora", "IL", "60505"),
    ("Rockford", "IL", "61101"), ("Peoria", "IL", "61602"), ("Springfield", "IL", "62701"),
    ("Milwaukee", "WI", "53202"), ("Madison", "WI", "53703"), ("Green Bay", "WI", "54301"),
    ("Minneapolis", "MN", "55401"), ("St Paul", "MN", "55102"), ("Duluth", "MN", "55802"),
    ("Des Moines", "IA", "50309"), ("Cedar Rapids", "IA", "52401"), ("Omaha", "NE", "68102"),
    ("Lincoln", "NE", "68508"), ("Kansas City", "MO", "64106"), ("St Louis", "MO", "63103"),
    ("Springfield", "MO", "65806"), ("Wichita", "KS", "67202"), ("Topeka", "KS", "66603"),
    ("Little Rock", "AR", "72201"), ("Fayetteville", "AR", "72701"), ("New Orleans", "LA", "70112"),
    ("Baton Rouge", "LA", "70802"), ("Shreveport", "LA", "71101"), ("Oklahoma City", "OK", "73102"),
    ("Tulsa", "OK", "74103"), ("Houston", "TX", "77002"), ("San Antonio", "TX", "78205"),
    ("Dallas", "TX", "75201"), ("Austin", "TX", "78701"), ("Fort Worth", "TX", "76102"),
    ("El Paso", "TX", "79901"), ("Arlington", "TX", "76010"), ("Corpus Christi", "TX", "78401"),
    ("Laredo", "TX", "78040"), ("Lubbock", "TX", "79401"), ("Denver", "CO", "80202"),
    ("Colorado Springs", "CO", "80903"), ("Aurora", "CO", "80012"), ("Albuquerque", "NM", "87102"),
    ("Las Cruces", "NM", "88001"), ("Phoenix", "AZ", "85004"), ("Tucson", "AZ", "85701"),
    ("Mesa", "AZ", "85201"), ("Glendale", "AZ", "85301"), ("Salt Lake City", "UT", "84101"),
    ("Provo", "UT", "84601"), ("Boise", "ID", "83702"), ("Billings", "MT", "59101"),
    ("Cheyenne", "WY", "82001"), ("Fargo", "ND", "58102"), ("Sioux Falls", "SD", "57104"),
    ("Las Vegas", "NV", "89101"), ("Reno", "NV", "89501"), ("Los Angeles", "CA", "90012"),
    ("San Diego", "CA", "92101"), ("San Jose", "CA", "95113"), ("San Francisco", "CA", "94103"),
    ("Fresno", "CA", "93721"), ("Sacramento", "CA", "95814"), ("Long Beach", "CA", "90802"),
    ("Oakland", "CA", "94607"), ("Bakersfield", "CA", "93301"), ("Riverside", "CA", "92501"),
    ("Stockton", "CA", "95202"), ("Portland", "OR", "97204"), ("Eugene", "OR", "97401"),
    ("Salem", "OR", "97301"), ("Seattle", "WA", "98104"), ("Spokane", "WA", "99201"),
    ("Tacoma", "WA", "98402"), ("Vancouver", "WA", "98660"), ("Anchorage", "AK", "99501"),
    ("Honolulu", "HI", "96813"),
]

AREA_CODES = {
    "MA": ["617", "508", "781"], "RI": ["401"], "CT": ["203", "860"], "NH": ["603"],
    "ME": ["207"], "VT": ["802"], "NJ": ["201", "609", "732"], "NY": ["212", "718", "585", "716"],
    "PA": ["215", "412", "610", "717"], "DE": ["302"], "MD": ["410", "301"], "DC": ["202"],
    "VA": ["703", "804", "757"], "WV": ["304"], "NC": ["704", "919", "336"], "SC": ["803", "843"],
    "GA": ["404", "706", "912"], "FL": ["305", "813", "407", "904"], "AL": ["205", "334"],
    "MS": ["601"], "TN": ["615", "901", "865"], "KY": ["502", "859"], "OH": ["614", "216", "513"],
    "MI": ["313", "616", "517"], "IN": ["317", "260"], "IL": ["312", "773", "815"],
    "WI": ["414", "608"], "MN": ["612", "651"], "IA": ["515", "319"], "NE": ["402"],
    "MO": ["816", "314", "417"], "KS": ["316", "785"], "AR": ["501", "479"], "LA": ["504", "225"],
    "OK": ["405", "918"], "TX": ["713", "210", "214", "512", "817", "915"], "CO": ["303", "719"],
    "NM": ["505", "575"], "AZ": ["602", "520", "480"], "UT": ["801"], "ID": ["208"],
    "MT": ["406"], "WY": ["307"], "ND": ["701"], "SD": ["605"], "NV": ["702", "775"],
    "CA": ["213", "619", "408", "415", "559", "916", "562", "510", "661", "951", "209"],
    "OR": ["503", "541"], "WA": ["206", "509", "253", "360"], "AK": ["907"], "HI": ["808"],
}

EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com",
                 "comcast.net", "verizon.net", "sbcglobal.net", "att.net", "msn.com", "live.com"]

EMPLOYERS = ["Walmart", "Amazon Fulfillment", "Target", "Kroger", "Home Depot", "UPS", "FedEx Ground",
             "Tyson Foods", "Aramark", "Marriott", "Dollar General", "AutoZone", "US Postal Service",
             "Regional Medical Center", "County School District", "City Public Works",
             "Frontier Trucking", "Sunrise Landscaping", "Precision Machining Inc",
             "Bright Star Home Care", "Lakeside Nursing", "Metro Transit Authority",
             "Blue Ridge Staffing", "Self Employed", "Unemployed", "Retired", "Disabled", "Student"]

# Bankruptcy courts, used for bankruptcy case numbers.
BK_DISTRICTS = ["EDNY", "SDNY", "NDIL", "CDCA", "NDTX", "MDFL", "EDPA", "NDGA", "EDMI", "DNJ",
                "SDOH", "WDWA", "DAZ", "EDCA", "MDNC"]
