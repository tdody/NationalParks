# NationalParks

<div class="container" style="padding-left: 100px;padding-right: 100px;padding-top: 60px; font-size: 13px;">

    <img src="{{ url_for('static', filename='img/icon/banner.jpg') }}" width="100%" alt="">
    <h2 class="mt-5" style="text-align: center;font-size: 30px;">About <span style="color: rgb(11, 75, 79)">usparks</span><span style="color: #dd872a">.io</span></h2>
    <h3 class="mt-5">Motivation
    </h3>
    Since visiting my first ever National Park, I have been fascinated by their diversity and the unique view the offer about the natural landscapes and biodiversity of the U.S. I have since visited 5 of them and I do not plan on stopping anytime soon. Through
    this project, I wanted to combine my passion of photography and machine learning to fuel my curiosity about the parks.
    <h3 class="mt-5">Goal
    </h3>
    Since President Ulysses S. Grant established Yellowstone as the first National Park in 1872, 61 other locations have joined the program. The National Parks are the best illustration of what the American ecosystem has to offer. Every year, the National
    Parks welcome more than 80 millions visitors. The goal of <span style="color: rgb(11, 75, 79)">usparks</span><span style="color: #dd872a">.io</span> is to transport visitors into the best locations of each park. <br>By using machine learning and
    clustering techniques, the application identify the most photographed location and gives the possibility to access some of these photographs. This application can be used as a tool to help you plan your upcoming trip to a National Park or simply to
    give you a virtual access to the most secluded ones.
    <h3 class="mt-5">Data
    </h3>
    The National Parks information was retrieved from the <a href="https://en.wikipedia.org/wiki/List_of_national_parks_of_the_United_States?oldformat=true">Wikipedia</a> page In order to make this project feasible, we needed access to a large dataset
    of geolocalized photographs. The website data was scrapped using the popular python library <a href="https://www.crummy.com/software/BeautifulSoup/">BeautifulSoup</a>. Once the initial information has been gathered for all 62 National Parks, the park
    boundaries were obtained from the official National Park Service <a href="https://www.nps.gov/planyourvisit/maps.htm">Website</a>. The obtained Geojson files are used to identify pictures that are taken inside each park.
    <br> The photographs were obtained using the <a href="https://www.flickr.com/services/api/">Flickr API</a>. For each park, we create a bounding box using the maximum and minimum longitude and latitude obtained from the Geojson files.
    <h3 class="mt-5">Clustering
    </h3>
    <div class="model_row">
        <div class="model_col_twothird">
            In order to identify the most visited locations, we used Density-Based Spatial Clustering of Applications with Noise (DBSCAN). The longitude and latitude of each photograph are used to cluster the photos. The DBSCAN algorithm takes two parameters. The
            first one in the maximum distance used to search neighbors and the second one is the minimum number of neighbors to be contained within the maximum distance to be considered a cluster.
            <br><br> As depicted on the image on the right, two clusters were obtained from the photo distribution with a minimum samples equal to 3. With four photos, cluster 1 is the most visited location. The two images on the top-right were not clustered
            because they do not meet the minimum sample requirement. The single phot on the bottom right is not assigned to any cluster as it is too isolated.
            <br><br>In order to find the best parameters, we define a metric of interest called the silhouette score.
            <br><br>For a data point $i \in C_{i}$ (data point $i$ in the cluster $C_{i}$), let $$a(i) = \frac{1}{|C_i| - 1} \sum_{j \in C_i, i \neq j} d(i, j)$$ </div>
        <div class=" model_col_third"><img src="{{ url_for('static', filename='/img/misc/clustering.png') }}" style="width: 100%;padding-left: 20px;"></div>
    </div>
    <div><br>be the mean distance between $i$ and all other data points in the same cluster, where $d(i, j)$ is the distance between data points $i$ and $j$ in the cluster $C_i$ (we divide by $|C_i| - 1$ because we do not include the distance $d(i, i)$ in
        the sum). We can interpret $a(i)$ as a measure of how well $i$ is assigned to its cluster (the smaller the value, the better the assignment). We then define the mean dissimilarity of point $i$ to some cluster $C_k$ as the mean of the distance
        from $i$ to all points in $C_k$ (where $C_k \neq C_i$). For each data point $i \in C_i$, we now define : $$b(i) = \min_{k \neq i} \frac{1}{|C_k|} \sum_{j \in C_k} d(i, j)$$ to be the ''smallest'' (hence the $\min$ operator in the formula) mean
        distance of $i$ to all points in any other cluster, of which $i$ is not a member. The cluster with this smallest mean dissimilarity is said to be the "neighboring cluster" of $i$ because it is the next best fit cluster for point $i$. We now define
        a ''silhouette'' (value) of one data point $i$ : $$s(i) = \frac{b(i) - a(i)}{\max\{a(i),b(i)\}} , if |C_i| > 1$$ and : $$s(i)=0 , if |C_i|=1 $$ </div>
    <h3 class="mt-5">Tags
    </h3>
    When a photo is uploaded by a user on Flickr, tags can be added manually to the post. Tags consist of words that are relevant to the photo (location, photo content). The tags are compiled for each cluster and sorted using the Term Frequency–Inverse Document
    Frequency (tf-idf). This summary of the most import tags is then provided on the cluster page to help describe the location corresponding to the cluster. The term frequency is defined as the number of times that term $t$ occurs in document $d$: $$tf(t,d)=f_{t,d}
    \Bigg/ {\sum_{t' \in d}{f_{t',d}}}$$ where:
    <br>&nbsp;&nbsp;$d$ is the document (list of tags associated to an image)<br>&nbsp;&nbsp;$t$ is the current tag
    <br><br>The inverse document frequency is the logarithmically scaled inverse fraction of the documents that contain the word (obtained by dividing the total number of documents by the number of documents containing the term, and then taking the logarithm
    of that quotient):$$ \mathrm{idf}(t, D) = \log \frac{N}{|\{d \in D: t \in d\}|}$$ where<br>&nbsp;&nbsp;$N$: total number of documents in the corpus $N = {|D|}$ <br>&nbsp;$ |\{d \in D: t \in d\}| $ : number of documents where the term $ t $ appears
    (i.e., $ \mathrm{tf}(t,d) \neq 0$). If the term is not in the corpus, this will lead to a division-by-zero. It is therefore common to adjust the denominator to $1 + |\{d \in D: t \in d\}|$.
    <br><br>Then tf–idf is calculated as:$$\mathrm{tfidf}(t,d,D) = \mathrm{tf}(t,d) \cdot \mathrm{idf}(t, D)$$
    <h3 class="mt-5">Architecture
    </h3>
    <figure>
        <p align="center">
            <img src="./static/img/misc/Architecture.png " alt="schema " , style="width:60% ">
        </p>
    </figure>
</div>