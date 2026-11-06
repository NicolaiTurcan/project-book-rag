# Five tests. The references are written by hand from the book and are deliberately
# demanding for recall: each needs several facts, and most of those facts sit in
# different chapters, so 4 retrieved chunks of 700 characters may not cover them all.
test_questions = [
    # two hops: Geppetto's sacrifice (ch. 9) and what Pinocchio did with the book
    (
        "What did Geppetto sell to buy Pinocchio an A-B-C book, and what did Pinocchio do with the book?",
        "Geppetto sold his old coat to buy the A-B-C book"
        "Pinocchio sold the book.",
    ),
    # a chain of events spread over several chapters
    (
        "How many gold pieces did Fire Eater give Pinocchio, and what happened to the gold pieces?",
        "Fire Eater gave Pinocchio five gold pieces for his father Geppetto. "
        "The Fox and the Cat persuaded him to bury them in the Field of Wonders so they would grow into a tree of gold. "
        "The Fox and the Cat dug up the gold pieces and stole them.",
    ),
    # paraphrased question: none of the book's key words ("woodpeckers", "Fairy") appear in it
    # (
    #     "After his face changed because he told untruths, how was it put back to normal?",
    #     "Pinocchio's nose grew longer with every lie he told the Fairy. "
    #     "The Fairy clapped her hands and a thousand woodpeckers flew in and pecked his nose back to its normal size.",
    # ),
    # # a long arc near the end of the book
    # (
    #     "What happened to Pinocchio and Lamp-Wick in the Land of Toys?",
    #     "Pinocchio ran away with his friend Lamp-Wick to the Land of Toys, where there was no school and every day was play. "
    #     "After some months they both grew donkey ears and turned into real donkeys. "
    #     "Pinocchio was sold to the owner of a circus.",
    # ),
    # # the reunion: needs the Shark, how long Geppetto was inside, and the escape
    # (
    #     "How does Pinocchio find Geppetto again, and how do they escape?",
    #     "Pinocchio is swallowed by the Terrible Shark and finds Geppetto living inside it. "
    #     "Geppetto had been inside the Shark for two years. "
    #     "Pinocchio carries Geppetto on his back out of the Shark's mouth while it sleeps, "
    #     "and the Tunny carries them to the shore.",
    # ),
    (
        "what does the fox say will happen if pinochio burries gold pieces?",
        "the fox says that the gold pieces would multiply. ",
    ),
    (
        "what is pinochio's wish for the fairy?",
        "to make him a real boy",
    ),
    (
        "what does the fairy say good boys do?",
        "good boys love to study"
        "good boys tell the truth"
        "good boys like to go to school",
    ),
]
