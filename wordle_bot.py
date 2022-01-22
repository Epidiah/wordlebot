#!/usr/bin/env python

import argparse
import re
from collections import Counter
from datetime import date
from random import sample


def set_words(wordle=None, save=False):
    with open('dictionary', 'r') as f:
        word_list = [ word.strip() for word in f.readlines() ]
    if wordle and wordle not in word_list:
        word_list.append(wordle)
        if save:
            with open('dictionary', 'a') as f:
                f.write(wordle)
    return word_list

def letter_counts(word_list):
    l_counter = Counter()
    l_counter_by_col = [Counter() for n in range(5)]
    for word in word_list:
        l_counter.update(word)
        for i,l in enumerate(word):
            l_counter_by_col[i][l] += 1
    return l_counter, l_counter_by_col

def mask(word, locked_col):
    return ''.join(
            l if i not in locked_col else ' ' for i,l in enumerate(word) 
        )

def test(wordle, guess):
    """
    0 means incorrect letter
    1 means correct letter in correct place
    2 means letter present in different place
    """
    result = [0, 0, 0, 0, 0]
    masking = []
    # First pass checks for greens and masks those
    # from the second pass
    for i,l in enumerate(guess):
        if l == wordle[i]:
            result[i] = 2
            masking.append(i)
    masked = mask(wordle, masking)
    # Second pass checks for yellows among the letters
    # that haven't been masked in the first pass
    for i,l in enumerate(guess):
        if i not in masking and l in masked:
            result[i] = 1
    return result
       
def emojinate(result):
    e = ''
    for i,r in enumerate(result):
        e += [':black_large_square:',':yellow_square:',':green_square:'][r]
        # if i < 4:
        #     e += chr(int('FEFF', 16))
    return e

def value_by_common_letters(word_list, locked_cols=None):
    """
    Calculates a value for each word prioritizing popular letters
    and not counting repeats.
    """
    lc, lcbc = letter_counts(word_list)
    ltotal = lc.total()
    lp = {k:v/ltotal for k,v in lc.items()}
    word_values = Counter()
    for word in word_list:
        word_values[word] = sum(lp[l] for l in set(word))
    return word_values

def value_by_columns(word_list, locked_cols=None):
    """
    Calculates a value for each word, prioritizing popular letters
    in their columns and ignoring columns already locked in.
    """
    if locked_cols == None:
        locked_cols = []
    lc, lcbc = letter_counts(word_list)
    ltotal = len(word_list)
    lps = [{k:v/ltotal for k,v in lcbc[n].items()} for n in range(5) if n not in locked_cols]
    word_values = Counter()
    for word in word_list:
        temp = (l for i,l in enumerate(word) if i not in locked_cols)
        word_values[word] = sum(lps[n][l] for n,l in enumerate(temp))
    return word_values

def random_value(word_list, locked_cols=None):
    """
    Assigns a random value to each word in a hail mary attempt to
    break out of wrong path.
    """
    wtotal = len(word_list)
    word_values = Counter({k:v for k,v in zip(sample(word_list,wtotal),range(wtotal))})
    return word_values

def winnow(word_list, guess, result, verbose=False):
    # First pass, lock in green cols and set prohibited letters
    # for all the black and yellow cols
    prohibited = [guess[i] for i,r in enumerate(result) if r==0]
    grep = '^'
    for i,r in enumerate(result):
        if r==2:
            grep += guess[i]
        else:
            grep +='[^'
            if r==1:
                grep += guess[i]
            grep += ''.join(prohibited) + ']'
    pattern = re.compile(grep)
    if verbose:
        print(f'Word List length before winnowing: {len(word_list)}')
        print(f"First pass with pattern: {grep}")
    word_list = [word for word in word_list if pattern.match(word)]
    if verbose:
        print(f'\tAfter first pass: {len(word_list)} words remaining...')
    # Final passes, to ensure the remaining words contain the
    # yellow letters somewhere, not counting green cols.
    yellow = [guess[i] for i,r in enumerate(result) if r==1]
    for y in yellow:
        word_list = [word for word in word_list if y in [w for i,w in enumerate(word) if result[i] != 2]]
        if verbose:
            print(f'\tSifting for words with "{y}"...')
            print(f'\t\t{len(word_list)} words remaining...')
    return word_list

def guestimate(word_list, round=0, previous=None, verbose=False):
    if not (round or previous):
        guess_func = sample(
            [
                value_by_common_letters,
                value_by_columns,
                random_value
            ],
            1
        )[0]
        guess = guess_func(word_list).most_common(1)[0][0]
        if verbose:
            print(f'Blind guess: {guess}')
        return guess
    else:
        guess = value_by_common_letters(word_list).most_common(1)[0][0]
        if verbose:
            print(f'Guess by most common remaining letters: {guess}')
        return guess

def ask(guess, attempt):
    print(f"Attempt {attempt}")
    print(f"I'm guessing: {guess.upper()}")
    while True:
        user_in = input("Hint (b/y/g): ")
        user_in = user_in.strip().lower()
        if len(user_in) != 5 or not set(user_in).issubset({'b','y','g'}):
            print("b = letter not in word\ny = letter not here, but in word\ng = letter here")
        else:
            return [{'b':0, 'y':1, 'g':2}[u] for u in user_in] 

def play(wordle='xxxxx', verbose=False, interactive=False):
    word_list = set_words()
    result = [0,0,0,0,0]
    guess = None
    guesses = []
    emojis = []
    while len(guesses) < 6 and sum(result) < 10:
        guess = guestimate(word_list, len(guesses), guess, verbose)
        guesses.append(guess)
        if interactive:
            result = ask(guess, len(guesses))
        else:
            result = test(wordle, guess)
        emojis.append(emojinate(result))
        word_list = winnow(word_list, guess, result, verbose)
    return guesses, emojis

def share(wordle, number, verbose=False):
    g,e = play(wordle, verbose)
    print(f'**Wordle Bot Got:**\nWordle {number}  {len(g)}/6\n')
    print('\n'.join(e))

def interactive(number, verbose=False):
    g,e = play(verbose=verbose, interactive=True)
    print(f'**Wordle Bot Got:**\nWordle {number}  {len(g)}/6\n')
    print('\n'.join(e))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Solves a solved Wordle")
    parser.add_argument('-s', '--solution', metavar='solution', type=str, help='Enter wordle solution.')
    parser.add_argument('-n', metavar='game number', type=int, help='Set the game number. Defaults to number of days since 6/19/2021.')
    parser.add_argument('-v','--verbose', action='store_true', help='Add to see how the bot progresses')
    parser.add_argument('-i', action='store_true', help='To play interactively.')
    args = parser.parse_args()
    if args.n:
        number = args.n
    else:
        number = (date.today() - date(2021, 6, 19)).days
    if args.i:
        interactive(number, verbose=args.verbose)
    else:
        if len(args.solution) != 5:
            parser.error("A wordle solution must contain exactly 5 letters.")
        if not args.solution.isalpha():
            parser.error("A wordle solution may only contain letters.")
        share(args.solution.lower(), number, verbose=args.verbose)
