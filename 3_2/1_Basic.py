import sys
import keyword
import operator
import datetime
import os

"""
..............................................................
print("Hello world!")
print(keyword.kwlist)
len(keyword.kwlist)
..............................................................
p2 = [ 'a','b','c']
print(p2)

p=10
if p==10:
    print("p is equal to 10")

for i in range(0,11):print(i)
..............................................................
def cube(n):
    return n**3
print(cube(2))
.............................................................
def evenodd(num):
    if num % 2 == 0 :
        print("Even Number")
    else:
        print("Odd Number")
evenodd(9)
print(evenodd.__doc__)
..............................................................
p=90
print(id(p))
print(hex(id(p)))
print(p, type(p), hex(id(p)))
..............................................................
intvar = 10
floatvar = 2.57
strvar = 'Python Language'
print(intvar, floatvar, strvar)

intvar, floatvar, strvar = 10, 3.47, "Pythin scripting"
print(intvar, floatvar, strvar)
..............................................................
val1 = 10
print(val1)
print(type(val1))
print(sys.getsizeof(val1))
print(val1, "is Inteeger?", isinstance(val1, int))

val3 = 25 + 10j
print(val3)
print(type(val3))
print(sys.getsizeof(val3))
print(val3, "is complex? ", isinstance(val3, complex))
..............................................................
bool1 = True
bool2 = False
print(type(bool1))
Tr = isinstance(bool2, bool)
print(Tr)

print(bool(0))
print(bool(1))
print(bool(False))
print(bool(None))
..............................................................
mystr = '''''Hello
            World!'''''
print(mystr)

str1 = ('Good '
        'Day '
        'Comming '
        'Soon ')
print(str1)

str2 = ' Woohoo'
str2 = str2*9
print(str2)
print(len(str2))
..............................................................
str3 = "Hello Python"
print( "First = ", str3[0], "\nLast = ", str3[-1])
print(str3[-4 : ])
str4 = "Labib"
print(str3[:5] +" "+ str4)
for i in str3:
    print(i)

for i in enumerate(str3):
    print(i)

print(list(enumerate(str3)))
..............................................................
str1 = "My favorite series is \"Mehmet Fatiller Sultan\""
print(str1)

str3 = "Hello Python"
print('Python' in str3)

str4 = "Natural language processing with Python and R and Java"
L = str4.partition("and")
print(L)
G = str4.rpartition("and")
print(G)
..............................................................
str1 = "           Hello Everyone                "
print(str1)
print(str1.strip())
print(str1.rstrip())
print(str1.lstrip())

str2 = "***********Hello Everyone*************"
print(str2)
print(str2.strip('*'))
print(str2.rstrip('*'))
print(str2.lstrip('*'))
..............................................................
str1 = "   Hello Everyone    "
print(str1.lower())
print(str1.upper())
print(str1.replace("lo" , "le"))

str1 = " one two three four five "
loc = str1.find("three")
print(loc)
..............................................................
str2 = "one two three four two one two five six one seven two"
print(str2)
print(str2.startswith("one"))
print(str2.endswith("three"))
print(str2.count("two"))
print(str2.split())

str3 = "one two three four four two one two four two one two five six one seven two five six one seven two two one two five six one seven two"
print(str3.rfind("one"))
print(str3.rindex("three"))
..............................................................
str3 = "Welcome Exveryone"
str3 = str3.center(70 , * ".")
print(str3)

str3 = str3.rjust(70 , * ".")
print(str3)
..............................................................
str1 = '123456789'
print(str1.isalpha())
print(str1.isalnum())
print(str1.isdecimal())
print(str1.isnumeric())

str2 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
print(str2.isupper())
print(str2.islower())
............................................................................................................................
list2 = [10.45, 55, 79.3, "Labib", ["apple", "orange", "banana"], "nazif", 15]
print(type(list2))
print(list2)
print(len(list2))
print(list2[-1])
print(list2[  : -1 ])

list1 = ['five', 'six', 'seven'] 
list3 = list1 + list2
print(list3)

for i in list3:
    print(i)

list4 = list1.extend(list2)
print(list4)

print(list1.reverse())
..............................................................
l1 = [1, 2, 3, 4, 5, 6, 7, 0, 8, 9]
print(all(l1))
print(any(l1))

l2 = "Welcome"
l3 = [i for i in l2]
print(l3)

list1 = [i for i in range(50) if i %2 == 1 ]
print(list1) 
..............................................................
import math
a = int(input("Enter first number: "))
b = int(input("Enter second number: "))
print("GCD =", math.gcd(a, b))
............................................................................................................................
a = int(input("Enter first number: "))
b = int(input("Enter second number: "))
while b != 0:
    r = a % b
    a = b
    b = r
print("GCD =", abs(a))
..............................................................

..............................................................

............................................................................................................................

..............................................................

............................................................................................................................

..............................................................

..............................................................

..............................................................

"""


































