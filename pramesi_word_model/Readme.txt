Pramesi Word Model
------------------

This is an adaption of RoboTrumpDNN from https://github.com/ppramesi/RoboTrumpDNN. It is written using
Keras in Python. It uses word2vec (https://radimrehurek.com/gensim/models/word2vec.html) followed by a
neural network with two levels of LSTM.

There are three steps to using the model:

1. Run build_dictionary.py to take the input text in "may_contributions.json" and create a word2vec model.
The model is saved in may2vec. Each word is represented as a 300 number vector.

2. Run train.py to train the model. This reads the text from may_contributions.json, the word2vec model
from may2vec and generates two files:

 - codetables.pickle. Words are represented by an integer code. This pickle file contains two dicts which
   map words to their code and vice versa.

  - trained_model.h5. This is a dump of the model and training weights. If present it is loaded when
   train.py is started so training can restart from where a previous run left off. It is saved every
   10 epochs during training. N.B. If you change the training data set or use less characters of it,
   you need to manually delete this file. This is the file that is used by create_sentence.py to run the
   model to create sentences.

3. Run create_sentence.py to test the model and create a sentence. You can give an argument with the
starting words. For instance:

   ./create_sentence.py "Surely, the right honourable gentleman cannot believe"

There are four trainings:

codetables_50k.pickle / trained_model_50k.h5 is a relatively brief training on the first 50k characters
of may_contributions.json.

codetables_50k2.pickle / trained_model_50k2.h5 is a full training on the first 50k characters
of may_contributions.json. Accuracy is 99.98%

codetables_500k.pickle / trained_model_500k.h5 is a full training on the first 500k characters
of may_contributions.json. Accuracy is 97.2%

codetables_4M.pickle / trained_model_4M.h5 is a full training on the whole of may_contributions.json.
This was done over the course of several days on a GPU machine on AWS. Accuracy is 84.0%

The learning rate (lr in the RMSprop constructor) needs to be reduced as training proceeds to stop
divergence.

The training to use is selected by the symbolic links codetables.pickle / trained_model.h5. For best
effect when demoing I am using 50k2.

The maybot code in the parent directory is designed to use this model and imports create_sentence.py
to call create_sentence().


The Model
---------

The input is 12 word vectors giving the previous 12 words of the sentence. The output is a one-hot
encoded next word code. If there are N unique words, the output is of width N.

                      Input: Previous words 
                                | (12, 300)
                              Dense
                                | (12, 500)
                      Batch Normalisation
                                | (12, 500)
                --------------------------------
                | (12, 500)                    | (12, 500)
               LSTM                      LSTM backwards
                | (12, 500)                    | (12, 500)
               LSTM                      LSTM backwards
                | (500)                        | (500)
                --------------   ---------------
                             |   |
                             merge
                               | (1000)
                      Batch Normalisation
                               | (1000)
                            Dropout
                               | (1000)
                             Dense
                               | (1500)
                              ELU
                               | (1500)
                      Batch Normalisation
                               | (1500)
                            Dropout
                               | (1500)
                             Dense
                               | (N)
                      Activation('softmax')                           
                               | (N)
                      Output: Next word code
