import random

# Collection of 50 stoic quotes focused on morals, hard work, and compassion
STOIC_QUOTES = [
    "The best revenge is not to be like your enemy. - Marcus Aurelius",
    "Waste no more time arguing what a good man should be. Be one. - Marcus Aurelius",
    "You have power over your mind - not outside events. Realize this, and you will find strength. - Marcus Aurelius",
    "When you arise in the morning, think of what a precious privilege it is to be alive - to breathe, to think, to enjoy, to love. - Marcus Aurelius", 
    "It is not death that a man should fear, but he should fear never beginning to live. - Marcus Aurelius",
    "The happiness of your life depends upon the quality of your thoughts. - Marcus Aurelius",
    "If it is not right, do not do it; if it is not true, do not say it. - Marcus Aurelius",
    "Our life is what our thoughts make it. - Marcus Aurelius",
    "Very little is needed to make a happy life; it is all within yourself, in your way of thinking. - Marcus Aurelius",
    "Do not indulge in dreams of having what you have not, but reckon up the chief of the blessings you do possess, and then thankfully remember how you would crave for them if they were not yours. - Marcus Aurelius",
    "The obstacle is the way. - Marcus Aurelius",
    "No man is free who is not master of himself. - Epictetus",
    "Make the best use of what is in your power, and take the rest as it happens. - Epictetus",
    "It's not what happens to you, but how you react to it that matters. - Epictetus",
    "Wealth consists not in having great possessions, but in having few wants. - Epictetus",
    "First say to yourself what you would be; and then do what you have to do. - Epictetus",
    "He who is not contented with what he has, would not be contented with what he would like to have. - Seneca",
    "We suffer more often in imagination than in reality. - Seneca",
    "Luck is what happens when preparation meets opportunity. - Seneca",
    "The greatest obstacle to living is expectancy, which hangs upon tomorrow and loses today. - Seneca",
    "Difficulties strengthen the mind, as labor does the body. - Seneca",
    "We are more often frightened than hurt; and we suffer more from imagination than from reality. - Seneca",
    "If a man knows not which port he sails, no wind is favorable. - Seneca",
    "Begin at once to live, and count each separate day as a separate life. - Seneca",
    "True happiness is to enjoy the present, without anxious dependence upon the future. - Seneca",
    "Sometimes even to live is an act of courage. - Seneca",
    "As is a tale, so is life: not how long it is, but how good it is, is what matters. - Seneca",
    "Life is long if you know how to use it. - Seneca",
    "If you really want to escape the things that harass you, what you're needing is not to be in a different place but to be a different person. - Seneca",
    "The wise man is neither raised up by prosperity nor cast down by adversity; for always he has strived to rely predominantly on himself. - Seneca",
    "All cruelty springs from weakness. - Seneca",
    "Just as I shall select my ship when I am about to go on a voyage, or my house when I propose to take a residence, so I shall choose my death when I am about to depart from life. - Seneca",
    "What man actually needs is not a tensionless state but rather the striving and struggling for some goal worthy of him. - Viktor Frankl",
    "The impediment to action advances action. What stands in the way becomes the way. - Marcus Aurelius",
    "You are afraid of dying. But, tell me, is the kind of life you lead really any different from being dead? - Seneca",
    "True good fortune is what you make for yourself. Good opportunities are what you create in your life. - Seneca", 
    "The soul becomes dyed with the color of its thoughts. - Marcus Aurelius",
    "He who fears death will never do anything worthy of a living man. - Seneca",
    "How long are you going to wait before you demand the best for yourself? - Epictetus",
    "If anyone tells you that a certain person speaks ill of you, do not make excuses about what is said of you but answer, 'He was ignorant of my other faults, else he would have not mentioned these alone.' - Epictetus",
    "Don't explain your philosophy. Embody it. - Epictetus",
    "You become what you give your attention to. - Epictetus",
    "External things are not the problem. It's your assessment of them. Which you can erase right now. - Marcus Aurelius",
    "How does it help to make troubles heavier by bemoaning them? - Seneca",
    "You are composed of three things: body, breath, and mind. Of these, the first two are yours insofar as they are only in your care. The third alone is truly yours. - Marcus Aurelius",
    "The key is to keep company only with people who uplift you, whose presence calls forth your best. - Epictetus",
    "Seek not the good in external things; seek it in yourselves. - Epictetus", 
    "The first rule is to keep an untroubled spirit. The second is to look things in the face and know them for what they are. - Marcus Aurelius",
    "Every hour focus your mind attentively on the performance of the task in hand, with dignity, human sympathy, benevolence and freedom, and leave aside all other thoughts. - Marcus Aurelius",
    "The art of living is more like wrestling than dancing. - Marcus Aurelius"
]

def get_random_quote():
    """Returns a random quote from the collection"""
    return random.choice(STOIC_QUOTES) 