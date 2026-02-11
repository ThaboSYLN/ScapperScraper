sport_Type =['Football',
'Basketball',
'Tennis',
'American Football',
'Baseball',
'Cricket',
'Ice Hockey',
'Handball',
'Volleyball',
'Rugby',
'Darts',
'Snooker',
'Table Tennis',
'MMA',
'Boxing',
'Cycling']
numbering = 0

#print(sport_Type ,  " ")
for i in sport_Type:
    numbering = numbering+1
    print(numbering,"",i)
userSelection = int(input("Refer to the number And type the one assocuated with the one you want: "))
spotHolder =sport_Type[userSelection-1]
print("Selected Sport: ",spotHolder )