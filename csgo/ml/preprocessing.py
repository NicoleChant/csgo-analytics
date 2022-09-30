from sklearn.pipeline import make_pipeline
from sklearn.compose import ColumnTransformer , make_column_transformer , make_column_selector
from sklearn.preprocessing import OneHotEncoder , MinMaxScaler , RobustScaler , FunctionTransformer
import pandas as pd
import os
import numpy as np
import pickle


def preprocess_features(X):
    
    def create_preprocessor():

        def transform_to_int(x):
            return x.applymap(int)

        def scale_time(x):
            time_min = 0.01 
            time_max = 175.0
            return (x - time_min)/(time_max - time_min)

        preproc_pipe = ColumnTransformer( 
              [ 
                ("time_left minmax scaler" , FunctionTransformer( scale_time ) , make_column_selector(dtype_include = np.float64))
            ]  , remainder = "passthrough")
        return preproc_pipe

    
    # print("Fetching data from GBQ...")
    # df = None
    # for data in get_all_gbq_data(os.environ.get("CHUNK_SIZE")):
    #     if df is None:
    #         df = data
    #         print(df.shape)
    #     else:
    #         df = pd.concat([ df , data] , axis = 0)
    #         print(df.shape)
    #         break

    maps = ['de_dust2', 'de_mirage', 'de_nuke', 'de_inferno', 'de_overpass',
            'de_vertigo', 'de_train', 'de_cache']

    dummies = {map_ : int(X['map'].iloc[0] == map_) for map_ in maps}
    X = pd.concat([ X.drop(columns = ['map']) , pd.DataFrame(dummies , index = [0]) ] , axis = 1)
    ordinal_columns = X.columns.drop(['time_left'])
    X[ordinal_columns] = X[ordinal_columns].astype(int)
        
    preproc_pipe = create_preprocessor()
    X_trans = preproc_pipe.fit_transform(X)
    return X_trans

if __name__ == "__main__": preprocess_features()