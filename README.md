# CSGO Round Winner Prediction Challenge

In this challenge you have to download the CSGO dataset from 
kaggle

<a href="https://www.kaggle.com/datasets/christianlillelund/csgo-round-winner-classification"> CSGO Round Winner Classification Dataset </a>

If you are using WSL, you can use the following to move:

bash 
```
mkdir data
unzip /mnt/c/Users/30697/Downloads/csgo_round_snapshots.csv.zip -d data
```

Let's check that everything is alright ✔️
```
cat data/csgo_round_snapshots.csv | head -n 10
```

Let's open the jupyter notebook

