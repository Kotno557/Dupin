<script>
import "leaflet/dist/leaflet.css";
import { LMap, LTileLayer, LCircle, LMarker, LPopup, LTooltip } from "@vue-leaflet/vue-leaflet";
import { Point, latLng} from "leaflet";
import L from "leaflet";
import axios from "axios";


export default {
  components: {
    LMap,
    LTileLayer,
    LCircle,
    LMarker,
    LPopup,
    LTooltip
  },
  data() {
    return {
      // for dupin
      local_ip: null,
      local_coord: latLng(0,0),
      local_country: null,

      target_url: null,
      target_ip: null,
      target_coord: latLng(0,0),

      clean_table_path: null,
      vpn_table_path: null,
      weight_table_path: null,

      direct_path_result: null,

      // for map drowing
      zoom: 5,
    };
  },
  methods: {
    target_detection(){
      const vm = this;
      axios.get(`http://localhost:8000/direct_path_check/?url=${this.target_url}`)
        .then(function(response) {
          console.log(response);
          vm.direct_path_result = response.data;
          vm.target_ip = response.data["target"]
          vm.target_coord = vm.getCoord(vm.target_ip)
        })
        .catch(function (error) {
          console.log(error);
        });
    },
    upload_file(type, event){
      let formData = new FormData();
      formData.append("file", event.target.files[0])
      axios.post(`http://localhost:8000/upload/${type}`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        .then(function (response) {
          console.log(response);
        })
        .catch(function (error) {
          console.log(error);
        });
    },
    isLocalInfoAlready(){
      if(this.local_ip != null && this.local_coord != latLng(0,0) && this.local_country != null){
        return true
      }
      return false
    },
    isTargetInfoAlready(){
      console.log("check")
      console.log(this.target_ip, this.target_coord)
      if(this.target_ip != null && this.target_coord != latLng(0,0)){
        return true
      }
      return false
    },
    getIcon(type) {
      let icon_url = {
        "local": "green",
        "target": "red",
        "select": "blue",
        "unchoose": "grey",
        "recommend": "gold"
      }
      let icon = new L.Icon({
        iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-${icon_url[type]}.png`,
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
      });
      return icon
    },
    getCoord(ip){
      const vm = this;
      let coord = null
      axios.get("https://api.incolumitas.com/")
        .then(function (response) {
          let res = response.data
          return latLng(res["location"]["latitude"], res["location"]["longitude"]);
        })
        .catch(function (error) {
          console.log(error);
        });
    }
  },
  mounted(){
    const vm = this;
    axios.get("https://api.incolumitas.com/")
      .then(function (response) {
        console.log(response);
        let res = response.data
        vm.local_ip = res.ip;
        console.log(vm.local_ip);
        vm.local_coord = latLng(res["location"]["latitude"], res["location"]["longitude"]);
        console.log(vm.local_coord);
      })
      .catch(function (error) {
        console.log(error);
      });
    
  }
};
</script>

<template>
  <div class="bg"> <!--body start-->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark p-3"> <!--navbar start-->
      <a class="navbar-brand" href="#"><i class="fa fa-bars"></i> <!-- 这里使用了Font Awesome的bars图标 --> Brand</a>
      <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav"
        aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav">
          <li class="nav-item">
            <a class="nav-link" href="#">CleanTable</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#">VPN Table</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#">WeightTable</a>
          </li>
        </ul>
      </div>
    </nav>
    <div class="bd-example m-3"> <!--Local info-->
      <h1>Your current IP is: {{local_ip}}.  Coordination: {{local_coord}}.  Contry: {{local_country}}</h1>
    </div>
    <div class="bd-example m-3"> <!--input area start-->
      <label for="formFile" class="form-label">
        CleanTable
      </label>
      <input class="form-control" type="file" id="formFile" accept="application/JSON" @change="upload_file(1, $event)">
      <label for="formFile" class="form-label mt-3">
        VPN Table
      </label>
      <input class="form-control" type="file" id="formFile" accept="application/JSON" @change="upload_file(2, $event)">
      <label for="formFile" class="form-label mt-3">
        WeightTable
      </label>
      <input class="form-control" type="file" id="formFile" accept="application/JSON" @change="upload_file(3, $event)">
      <label for="formFile" class="form-label mt-3">
        Which webpage would you like to browse. Simply enter the domain name part, such as: "google.com", "aws.amazon.com".
      </label>
      <input v-model="target_url" class="form-control" type="url" id="formFile">
      <button v-on:click="target_detection" type="button" class="btn btn-primary mt-3">Detection</button>
    </div>
    <div class="bd-example m-3"> <!--detect map start-->
      <div class="map">
          <div style="height:600px; width:800px">
            <l-map ref="map" v-model:zoom="zoom" :center="local_coord">
              <l-tile-layer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                layer-type="base"
                name="OpenStreetMap"
              ></l-tile-layer>
              <l-marker v-if="local_ip != null" :lat-lng="local_coord" :icon="getIcon('local')">
                <l-tooltip :options="{ permanent: true, direction: 'bottom'}">
                  you
                </l-tooltip>
              </l-marker>
              <l-marker v-if="target_ip != null" :lat-lng="target_coord" :icon="getIcon('target')">
                <l-tooltip :options="{ permanent: true, direction: 'bottom'}">
                  {{target_url}}
                </l-tooltip>
              </l-marker>
            </l-map>
          </div>
      </div>
    </div>

  </div> <!--body end-->
</template>

<style scoped>
.bg {
  font-family: Arial, sans-serif;
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow-y: auto;
  background-color: rgb(222, 220, 220);
}

.bd-example {
  position: relative;
  padding: 1rem;
  border: solid #4f4a4a;
  border-width: 1px;
  border-radius: 0.25rem;
}

.map {
  height: 600px;
}
</style>