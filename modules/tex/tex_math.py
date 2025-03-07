# -*- coding: utf-8 -*-
"""
Created on Fri Mar  7 17:35:09 2025

@author: Asterisk
"""

#Size of a texture packet in bytes
packetSize = 16

#Round up Divide
def ruD(x,y):
    """ Rounded Up Integer Division
    Parameters
    ----------
    x : Int
        Dividend
    y : Int
        Divisor
    
    Returns
    ----------
    quotient : Int
        Result of operation
    """
    return (x+y-1)//y

#Round up to Next Multiple
def ruNX(x,y):
    """ Round Up to Next Multiple
    Parameters
    ----------
    x : Int
        Number to Round Up
    y : Int
        Target which we want a multiple off greater than x
    
    Returns
    ----------
    x_prime : Int
        Smallest value of a such that a*y >= x
    """
    return ruD(x,y)*y

def product(listing):
    """ Multiplies all of the list inputs
    Parameters
    ----------
    listing : List
        Inputs to be foldl with (*)
    
    Returns
    ----------
    prod : Int
        Result of multiplying all of the list elements sequentially
    """
    cur = 1
    for element in listing:
        cur *= element
    return cur

def bitCount(int32):
    """ Counts number of bits set
    Parameters
    ----------
    int32 : Int
        Int to count number of bits set
    
    Returns
    ----------
    sum : Int
        Number of Bits set
    """
    return sum(((int32 >> i) & 1 for i in range(32)))

def dotDivide(num,denom):
    """ Component-wise Vector pair division
    Parameters
    ----------
    num : Float [N]
        Numerator Vector
    denom : Float [N]
        Denominator Vector
    Returns
    ----------
    result : Float [N]
        Result vector
    """
    return tuple([ruD(vl,vr) for vl,vr in zip(num,denom)])