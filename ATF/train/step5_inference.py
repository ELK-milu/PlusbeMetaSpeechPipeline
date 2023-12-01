import tensorflow as tf
import numpy as np
import os


# step5 TensorFlow Lite 正向推理阶段
class tfliteInference:
    """ Inference with tflite model
    Args:
        model_path: str, the path of the tflite model
        pb_model_path: str, the path of the pb model, if not None, convert the pb model to tflite model
    """

    def __init__(self, model_path, pb_model_path=None, NpyPath='./', Index="demo", SavePath='./'):
        self.model_path = model_path
        if not os.path.exists(model_path):
            # if pb_model_path is not None:
            self.convert_to_tflite(pb_model_path)
        # Load the model
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        # Set model input
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.NpyPath = NpyPath
        self.SavePath = SavePath
        self.Index = str(Index)

    def convert_to_tflite(self, pb_model_path):
        # Convert the model from saved model(.pb) to tflite
        converter = tf.lite.TFLiteConverter.from_saved_model(pb_model_path)
        tflite_model = converter.convert()
        with open(self.model_path, "wb") as f:
            f.write(tflite_model)
        print(f'Save TFLite model to {self.model_path} successfully!')

    def run(self, inputData):
        # Preprocess the image before sending to the network.
        inputData = np.expand_dims(inputData, axis=0)

        # The actual detection.
        self.interpreter.set_tensor(self.input_details[0]["index"], inputData)
        self.interpreter.invoke()

        # Save the results.
        output = self.interpreter.get_tensor(self.output_details[0]["index"])[0]
        return output

    def get_weight(self, data, label_len=37):
        # weight = self.run(data)
        weight = np.zeros((data.shape[0], label_len))
        # weight = []
        for i in range(data.shape[0]):
            data_temp = data[i].astype(np.float32)
            # data_temp = data_temp.reshape((32,64,1))
            output = self.run(data_temp).copy()
            weight[i] = output
        return weight


def OnTake(thisTF, data=None, _callback=None):
    # tflitepath = '../test/AiSpeech/best_model/Audio2Face.tflite'
    # model_path = '../test/AiSpeech/best_model/Audio2Face'
    if data is None:
        data = np.load(os.path.join(thisTF.NpyPath + thisTF.Index + ".npy"))
    weight = thisTF.get_weight(data)
    print(weight.shape)

    np.set_printoptions(threshold=np.inf)
    with open(thisTF.SavePath + thisTF.Index + '.txt', 'w') as f:
        for i in range(weight.shape[0]):
            f.write(str(weight[i]) + '\n')
        print(f'Write weight successfully!')
    if _callback is not None:
        try:
            _callback(thisTF.Index + '.txt')
        except Exception as e:
            print("step4 ATF inference Wrong:", e)


if __name__ == "__main__":
    tflitepath = '../AiSpeech/best_model/Audio2Face.tflite'
    model_path = '../AiSpeech/best_model/Audio2Face'
    # tflitepath = './output7_11/models/Audio2Face.tflite'
    # model_path = './output7_11/models/Audio2Face'

    inference = tfliteInference(tflitepath, model_path)
    data = np.load(os.path.join('./lpc/1.npy'))

    weight = inference.get_weight(data)
    print(weight.shape)

    np.set_printoptions(threshold=np.inf)
    with open('./1.txt', 'w') as f:
        for i in range(weight.shape[0]):
            f.write(str(weight[i]) + '\n')
        print(f'Write weight successfully!')
