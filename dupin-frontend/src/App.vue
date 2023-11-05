<script>
import "leaflet/dist/leaflet.css";
import { LMap, LTileLayer, LCircle, LMarker, LPopup, LTooltip, LPolyline } from "@vue-leaflet/vue-leaflet";
import { Point, latLng } from "leaflet";
import L from "leaflet";
import axios from "axios";

import {Modal} from "bootstrap"

let modal;

export default {
  components: {
    LMap,
    LTileLayer,
    LCircle,
    LMarker,
    LPopup,
    LTooltip,
    LPolyline
  },
  data() {
    return {
      direct_data: {
        "local":{
          "ip": null,
          "coord": latLng(0,0),
          "type": "local"
        },
        "target":{
          "url": null,
          "ip": null,
          "coord": latLng(0,0),
          "type": "target"
        },
        "line":{
          "point": null,
          "node": null,
          "weight": null,
          "summary": null,
          "color": "red"
        }
      },
      modal_data: {
        "switch": false,
        "title": null,
        "data": {}
      },
      vpn_data: {
        "path": {},
        "show_path": {},
        "vpn_node": {}, // 2023/11/06 here
        "select": [],
        "now": null
      },
      local_zoom: 5,
      vpn_zoom: 5,
      loading: false
    };
  },
  methods: {
    async target_detection(){
      this.loading = true
      try{
        var dupin_result = await axios.get(`http://localhost:8000/direct_path_check/?url=${this.direct_data.target.url}`)
        this.direct_data.target.ip = dupin_result.data["target"]["ip"]
        this.direct_data.line.node = dupin_result.data["node"]
        this.direct_data.line.weight = dupin_result.data["weight"]
        this.direct_data.line.summary = dupin_result.data["summary"]
      }
      catch(error){
        console.log(error)
      }
      try{
        var ipinfo_result = await axios.get(`https://ipinfo.io/${this.direct_data.target.ip}/json?token=6c37228d8bfabd`)
        this.direct_data.target.coord = latLng(ipinfo_result.data["loc"].split(",").map(Number))
        this.direct_data.line.point = [this.direct_data.local.coord, this.direct_data.target.coord]
      }
      catch(error){
        console.log(error)
      }
      this.loading = false
    },
    async vpn_detection(){
      this.loading = true
      try{
        var dupin_vpn_result = await axios.get(`http://localhost:8000/vpn_path_check/?target_url=${this.direct_data.target.url}`)
        this.vpn_data.path = dupin_vpn_result.data
      }
      catch(error) {
        console.log(error)
      }
      this.loading = false
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
    showModal(start, end, data){
      this.modal_data.title = `Path Detection: ${start} → ${end}, Weight ${this.modal_data.data.weight}`
      this.modal_data.data = data

      modal.show()
    }
  },
  mounted(){
    const vm = this;
    axios.get(`https://ipinfo.io/json?token=6c37228d8bfabd`)
      .then(function (response) {
        vm.direct_data.local.ip = response.data["ip"]
        vm.direct_data.local.coord = latLng(response.data["loc"].split(",").map(Number))
      })
      .catch(function (error) {
        console.log(error);
      });
    modal = new Modal(document.getElementById("staticBackdrop"))
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
      <h1>Your current IP is: {{direct_data.local.ip}}.  Coordination: {{direct_data.local.coord}}.</h1>
      <p>Debugger: {{direct_data}} </p>
      <p>{{vpn_data}}</p>
    </div>
    <div class="bd-example m-3"> <!--input area start-->
      <form class="row g-3">
        <div class="col-md-4">
          <label for="formFile" class="form-label">
            *CleanTable
          </label>
          <input class="form-control" type="file" id="formFile" accept="application/JSON" @change="upload_file(1, $event)">
        </div>
        <div class="col-md-4">
          <label for="formFile" class="form-label">
            *VPN Table:
          </label>
          <input class="form-control" type="file" id="formFile" accept="application/JSON" @change="upload_file(2, $event)">
        </div>
        <div class="col-md-4">
          <label for="formFile" class="form-label">
            *WeightTable:
          </label>
          <input class="form-control" type="file" id="formFile" accept="application/JSON" @change="upload_file(3, $event)">
        </div>
        <div class="col-md-8">
          <label for="formFile" class="form-label">
            *Which webpage would you like to browse. Simply enter the domain name part:
          </label>
          <input v-model="direct_data.target.url" class="form-control" type="url" id="formFile" placeholder="'google.com', 'aws.amazon.com', 'microsoft.com', and etc.">
        </div>
        <div class="col-md-4">
          <label for="formFile" class="form-label">
            IPinfo token (optional):
          </label>
          <input class="form-control" type="text" placeholder="6c3********abd">
        </div>
        <div class="col-md-12">
          <button v-on:click="target_detection" type="button" class="btn btn-primary mt-3">Detection</button>
        </div>
      </form>
    </div>

    <div class="bd-example m-3"> <!--detect map start-->
      <div class="row g-1">
        <div class="col">
          <div class="map">
            <div style="height:600px; width:800px">
              <l-map ref="map" v-model:zoom="local_zoom" :center="direct_data.local.coord">
                <l-tile-layer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  layer-type="base"
                  name="OpenStreetMap"
                ></l-tile-layer>
                <l-marker v-if="direct_data.local.ip" :lat-lng="direct_data.local.coord" :icon="getIcon(direct_data.local.type)">
                  <l-tooltip :options="{ permanent: true, direction: 'bottom'}">
                    you
                  </l-tooltip>
                </l-marker>
                <l-marker v-if="direct_data.target.ip" :lat-lng="direct_data.target.coord" :icon="getIcon(direct_data.target.type)" >
                  <l-tooltip :options="{ permanent: true, direction: 'bottom'}">
                    {{direct_data.target.url}}
                  </l-tooltip>
                </l-marker>
                <l-polyline v-if="direct_data.line.point" :lat-lngs="direct_data.line.point" :color="direct_data.line.color" >
                  <l-tooltip :options="{ permanent: true, interactive: true}" >
                    <span @click="showModal(direct_data.local.ip, direct_data.target.ip, direct_data.line.node)" class="border border-primary rounded fs-6" :title="JSON.stringify(direct_data.line.summary,null, 4)">
                      {{direct_data.line.weight}}
                    </span>
                  </l-tooltip>
                </l-polyline>
              </l-map>
            </div>
          </div>
        </div>
        <div class="col">
          <div class="h-100 w-100 d-flex align-items-center justify-content-center">
            <button class="btn btn-primary" @click="vpn_detection">>VPN 路線偵測></button>
          </div>
        </div>
        <div class="col">
          <div class="map">
            <div style="height:600px; width:800px">
              <l-map ref="map" v-model:zoom="vpn_zoom" :center="direct_data.local.coord">
                <l-tile-layer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  layer-type="base"
                  name="OpenStreetMap"
                ></l-tile-layer>
              </l-map>
            </div>
          </div>
        </div>
      </div>
    </div>
    

    <!-- Modal -->
    <div class="modal fade" id="staticBackdrop" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1" aria-labelledby="staticBackdropLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="staticBackdropLabel">
              {{modal_data.title}}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <table class="table table-striped table-bordered table-hover">
              <thead>
                <tr>
                  <th scope="col" v-for="head in ['IP', 'Level', 'Weight', 'hdm', 'isp', 'os']">
                    <strong>
                      {{head}}
                    </strong>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="key in Object.keys(modal_data.data)">
                  <td v-for="item in [key, modal_data.data[key].level, modal_data.data[key].single_weight, modal_data.data[key].hdm, modal_data.data[key].isp, modal_data.data[key].os]">
                    {{ item !== "" ? item : "N/A" }}
                  </td>
                </tr>
              </tbody>
            </table>
            
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>

  </div> <!--body end-->

  <div id="dimScreen" v-if="loading">
    <div class="h-100 w-100 d-flex align-items-center justify-content-center">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
  </div>
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

html, body {
    height: 100%;
    margin: 0px;
}

#dimScreen
{
    width: 100%;
    height: 100%;
    background:rgba(255,255,205,0.5);
    position: fixed;
    top: 0px;
    left: 0px;
    z-index: 1000;
}
</style>