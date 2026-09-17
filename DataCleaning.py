def getDaysSincePublic(stringDate) -> int:
    cumulativeDays = 0
    listDate = stringDate.split("/")
    day, month, year = listDate[0:3]
    day, month, year = int(month), int(day), int(year)
    monthsLeap = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
    monthsNonLeap = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

    if (year == 2024):
        cumulativeDaysSince2024 = monthsLeap[month] + day
    else: 
        cumulativeDaysSince2024 = 366 + max(0, (year - 2025) * 366) + monthsNonLeap[month] + day

    # 986 days from jan1 2024 till sep10 2026
    # hence 986 - cumulative days = days from sep10 

    return (986 - cumulativeDaysSince2024)

file2024 = open("IPO_DATASET(2024_IPO_PRICING).csv", 'r')
file2025 = open("IPO_DATASET(2025_IPO_PRICING).csv", 'r')
file2026 = open("IPO_DATASET(2026_IPO_PRICING).csv", 'r')

files = [file2026, file2025, file2024]

intergratedFile = []
for file in files:
    firstLine = True
    for row in file:
        if firstLine == True:
            firstLine = False
            continue
        
        individualIPODict = {}
        row = row.split(",")
        ticker, industry, date, shares, offerPrice, firstDayClose, currrentPrice = row[1:8]

        shares = float(shares)
        offerPrice = int(float(offerPrice.strip("$"))*100)
        firstDayClose = int(float(firstDayClose.strip("$"))*100)
        currentPrice = int(float(currrentPrice.strip("$"))*100)
        offerPrice = int(float(offerPrice.strip("$"))*100)
        dateList = date.split("/")
        date = f"{dateList[1]}/{dateList[0]}/{dateList[2]}"
        returnPercent = ((currrentPrice - offerPrice)/offerPrice) * 100
        daysSincePublic = getDaysSincePublic(date)
        
        individualIPODict = {
            "Ticker":ticker, "Industry":industry, "Date":date,
            "Shares":shares, "OfferPrice":offerPrice, "FirstDayClose":firstDayClose, "CurrentPrice":CurrentPrice, "Return":returnPercent, 
            "DaysSincePublic":daysSincePublic
        }
        
        intergratedFile.append(individualIPODict)


print(intergratedFile)







