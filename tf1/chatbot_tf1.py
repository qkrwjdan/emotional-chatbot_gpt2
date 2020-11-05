import json
import os
import numpy as np
import tensorflow as tf

from tf1 import encoder
from tf1 import model
from tf1 import sample

def interact_model(
    temperature,
    top_k,
    top_p,
    nsamples,
    batch_size,
    length,
    seed=None,
):

    models_dir = os.path.expanduser(os.path.expandvars('./models'))
    if batch_size is None:
        batch_size = 1
    assert nsamples % batch_size == 0

    enc = encoder.get_encoder('345M_org', models_dir)
    hparams = model.default_hparams()
    with open(os.path.join('./models', '345M_org', 'hparams.json')) as f:
        hparams.override_from_dict(json.load(f))

    if length is None:
        length = hparams.n_ctx // 2
    elif length > hparams.n_ctx:
        raise ValueError("Can't get samples longer than window size: %s" % hparams.n_ctx)

    with tf.Session(graph=tf.Graph()) as sess:
        context = tf.placeholder(tf.int32, [batch_size, None])
        np.random.seed(seed)
        tf.set_random_seed(seed)
        output = sample.sample_sequence(
            hparams=hparams, length=length,
            context=context,
            batch_size=batch_size,
            temperature=temperature, top_k=top_k, top_p=top_p
        )

        saver = tf.train.Saver()
        ckpt = tf.train.latest_checkpoint(os.path.join('./models', '345M_org'))
        saver.restore(sess, ckpt)

        raw_text = '<|endofdlg|>'
        print('#'*20+ ' Start the Chatting '+'#'*20)
        while True:
            utterances = input("user: ")
            raw_text +='\n' + 'user: '+ utterances  + '\n' + 'bot: '

            context_tokens = enc.encode(raw_text)
            generated = 0
            for _ in range(nsamples // batch_size):
                out = sess.run(output, feed_dict={
                    context: [context_tokens for _ in range(batch_size)]
                })[:, len(context_tokens):]
                for i in range(batch_size):
                    generated += 1
                    text = enc.decode(out[i])
                    result=list(text.partition('\n'))
                    print('bot:' + result[0])
                    raw_text += str(result[0])


