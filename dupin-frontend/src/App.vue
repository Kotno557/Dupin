<script>
import "leaflet/dist/leaflet.css";
import { LMap, LTileLayer, LCircle } from "@vue-leaflet/vue-leaflet";
import axios from 'axios';


export default {
  components: {
    LMap,
    LTileLayer,
    LCircle
  },
  data() {
    return {
      // for dupin
      target_url: "",
      clean_table_path: "",
      vpn_table_path: "",
      weight_table_path: "",

      // for map drowing
      zoom: 3,
      circle: {
        center: [25.033671, 121.564427],
        radius: 4500,
        color: 'red'
      }
    };
  },
  methods: {
    target_detection(target_url){
      
    },
    upload_file(type, event){
      let formData = new FormData()
      switch(type){
        case 1: // ClEAN_TABLE
          console.log("Clean_table");
          formData.append("file", event.target.files[0])
          break;
        case 2: // VPN_TABEL
          console.log("VPN" + event.target.files[0])
          break;
        case 3: // WEIGHT_TABLE
          console.log("WEIGHT" + event.target.files[0])
          break;
        default:
          console.log("ERROR!!")
      }
    }
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
      <button v-on:click="upload_file" type="button" class="btn btn-primary mt-3">Detection</button>
    </div>
    <div class="bd-example m-3"> <!--detect map start-->
      <div class="map">
        <l-map ref="map" v-model:zoom="zoom" :center="[25.033671, 121.564427]">
          <l-tile-layer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" layer-type="base"
            name="OpenStreetMap"></l-tile-layer>
          <l-circle :lat-lng="circle.center" :radius="circle.radius" :color="circle.color" />
        </l-map>
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



  .map {
    height: 360px;
  }
}
</style>