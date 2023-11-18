<script>
import "leaflet/dist/leaflet.css";
import { LMap, LTileLayer, LCircle, LMarker, LPopup, LTooltip, LPolyline } from "@vue-leaflet/vue-leaflet";
import L from "leaflet";
import axios from "axios";

import {Modal} from "bootstrap"

let modal;
let welcon_modal
let clean_modal
let vpn_modal
let weight_modal

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
          "coord": [0,0],
          "type": "local"
        },
        "target":{
          "url": null,
          "ip": null,
          "coord": [0,0],
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
        "node": {},
        "select": [] /*["20.84.80.216","20.199.51.125","74.226.208.130"]*/,
        "now": null
      },
      cleantable:{
        all_table: null,
        res:{
          "hdm":{
            "clean": [],
            "unclean": []
          },
          "isp":{
            "clean": [],
            "unclean": []
          }
        },
        isp:{
          focus: "",
          show: {}
        }
      },
      local_zoom: 5,
      vpn_zoom: 5,
      loading: false,
      p_disconnect: false
    };
  },
  methods: {
    async target_detection(){
      this.loading = true

      var dupin_result
      var ipinfo_result
      try{
        dupin_result = await axios.get(`http://localhost:8000/direct_path_check/?url=${this.direct_data.target.url}`)
        this.direct_data.target.ip = dupin_result.data["target"]["ip"]
        
        ipinfo_result = await axios.get(`https://ipinfo.io/${this.direct_data.target.ip}/json?token=6c37228d8bfabd`)
      
        this.direct_data.target.coord = ipinfo_result.data["loc"].split(",").map(Number)
        this.direct_data.line.node = dupin_result.data["node"]
        this.direct_data.line.weight = dupin_result.data["weight"]
        this.direct_data.line.summary = dupin_result.data["summary"]
        this.direct_data.line.point = dupin_result.data["draw_path"]
        
        this.loading = false
      }
      catch(error){
        console.log(error)
        // Handle the error, for example, set default values or show an error message.
      }
    },
    async vpn_detection(){
      function findForth(n, top, bottom) {
        // 確保 top <= bottom
        if (top > bottom) {
          [top, bottom] = [bottom, top];
        }

        // 計算每一等份的範圍
        const range = (bottom - top + 1) / 4;

        // 計算 n 在哪個等份
        const interval = Math.floor((n - top) / range) + 1;

        if (interval == 1){
          return "#008000"
        }
        else if (interval == 2){
          return "#FFFF00"
        }
        else if (interval == 3){
          return "#FFA500"
        }
        else if (interval == 4){
          return "#FF0000"
        }
        else{
          return "#B6B6B6"
        }
      }

      this.loading = true
      try{
        var dupin_vpn_result = await axios.get(`http://localhost:8000/vpn_path_check/?target_url=${this.direct_data.target.url}`)
        this.vpn_data.path = dupin_vpn_result.data

        this.vpn_data.now = "localhost"
        this.vpn_data.node["localhost"] = {
          "name" : `localhost(${this.direct_data.local.ip})`,
          "coord": this.direct_data.local.coord,
          "type": this.direct_data.local.type
        }
        this.vpn_data.node[`${this.direct_data.target.url}`] = {
          "name" : `${this.direct_data.target.url}`,
          "coord": this.direct_data.target.coord,
          "type": this.direct_data.target.type
        }
        // node view data
        for (const [key, value] of Object.entries(this.vpn_data.path)) {
          if (key != "localhost") {
            var ipinfo_result = await axios.get(`https://ipinfo.io/${key}/json?token=6c37228d8bfabd`)
            var vpn_name = `VPN${key}`
            this.vpn_data.node[key] = {
              "name": vpn_name,
              "ip": key,
              "coord": ipinfo_result.data["loc"].split(",").map(Number),
              "type": "enable",
              "show": true
            }
          }
        }
        
        // for edge
        var max_weight = Number.MIN_SAFE_INTEGER
        var min_weight = Number.MAX_SAFE_INTEGER
        for (const [key, value] of Object.entries(this.vpn_data.path)) {
          for (const [key2, value2] of Object.entries(this.vpn_data.path[key])) {
            max_weight = Math.max(max_weight, value2.path_weight)
            min_weight = Math.min(min_weight, value2.path_weight)
          }
        }
        console.log("color", max_weight, min_weight)
        for (const [key, value] of Object.entries(this.vpn_data.path)) {
          this.vpn_data.show_path[key] = {}
          for (const [key2, value2] of Object.entries(this.vpn_data.path[key])) {            
            this.vpn_data.show_path[key][key2] = {
              // "points": value2.draw_path,
              "points": [this.vpn_data.node[key].coord, this.vpn_data.node[key2].coord],
              "color": findForth(value2.path_weight, max_weight, min_weight),
              "weight": value2.path_weight,
              "data": value2.info,
            }

          }
        }
      }
      catch(error) {
        console.log(error)
      }
      this.loading = false
      alert("The VPN path scan has been completed. Please click on the grey VPN coordinates to determine the connection path. \nThe yellow path represents the shortest weighted path for your reference. Once you have made your selection, please click on the 🔗 button to initiate the connection.")
    },
    async connect(){
      function delay(milliseconds){
        return new Promise(resolve => {
          setTimeout(resolve, milliseconds);
        });
      }
      this.loading = true
      try{
        await axios.post(`http://localhost:8000/connect/?target_url=${this.direct_data.target.url}`, this.vpn_data.select)
      }
      catch(e){
        console.log("there is a catch of 500 ERR")
        await delay(20000)
        console.log("delay 20sec")
        
        var ip_now 
        var p = 0
        do{
          try{
            p += 1
            ip_now = (await axios.get("http://localhost:8000/ip/")).data["ip"]
            console.log(ip_now, "vs", this.direct_data.local.ip)
            await delay(5000)
          }
          catch(e){
            console.log(e)
          }
        }while(ip_now == this.direct_data.local.ip && p <= 3)
        
        if (p > 3){
          alert(`The connection fail, please check the backend log to get more info`)
        }
        else{
          this.p_disconnect = true
          alert(`New connection has been established.\n\n
          IP of loacal from:\n\n
          ${this.direct_data.local.ip} → ${ip_now}\n\n
          Enjoy Your Clean Connection Uwu`)
        }
        this.loading = false
      }
    }, 
    async disconnect() {
      this.loading = true
      try{
        await axios.get("http://localhost:8000/disconnect")
      }
      catch(e){
        console.log(e)
      }
      setTimeout(function () {
        console.log("wating 5 sec...")
      }, 5000)
      this.loading = false
      alert("The connection data has been stored in the history. If you want to connect directly with the same settings, please go to the connection history")
      location.reload()
    },
    update_now (node_new) {
      console.log("click"+node_new)
      if (node_new === this.direct_data.target.url || node_new === "localhost") {
        return
      }
      this.vpn_data.select.push(node_new)
      this.vpn_data.node[node_new].type = "disable"
      //this.vpn_data.show_path[]
    },
    redo(){
      console.log("back")
      let last = this.vpn_data.select[this.vpn_data.select.length - 1]
      this.vpn_data.node[last].type = "enable"
      this.vpn_data.select.pop()
    },
    path_clear(){
      while (this.vpn_data.select.length > 0){
        this.redo()
      }
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
    getIcon(type) {
      let icon_url = {
        "local": "green",
        "target": "red",
        "disable": "blue",
        "enable": "grey",
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
      this.modal_data.title = `Path Detection: ${start} → ${end}, Weight ${this.direct_data.line.weight}`
      this.modal_data.data = data

      modal.show()
    },
    startWelcome(){
      clean_modal.show()
    },
    startVPNTable(){
      vpn_modal.show()
    },
    startWeightTable(){
      weight_modal.show()
    }
  },
  mounted(){
    const vm = this;
    axios.get(`https://ipinfo.io/json?token=6c37228d8bfabd`)
      .then(function (response) {
        vm.direct_data.local.ip = response.data["ip"]
        vm.direct_data.local.coord = response.data["loc"].split(",").map(Number)
      })
      .catch(function (error) {
        console.log(error);
      });
    modal = new Modal(document.getElementById("staticBackdrop"))
    welcon_modal = new Modal(document.getElementById("welcom_modal"))
    clean_modal = new Modal(document.getElementById("CleanTable"))
    vpn_modal = new Modal(document.getElementById("VPNTable"))
    weight_modal = new Modal(document.getElementById("WeightTable"))
    welcon_modal.show()
    axios.get(`http://localhost:8000/brand_list`)
      .then(function (response) {
        vm.cleantable.all_table = response.data
        console.log(`[INFO] Get brand_list hdm size = ${vm.cleantable.all_table.hdm.length}, isp size = ${Object.keys(vm.cleantable.all_table.isp).length}`)
        console.log(vm.cleantable.all_table)
        for(let key of Object.keys(vm.cleantable.all_table["isp"])){
          vm.cleantable.isp.show[key] = []
          for(let provider of vm.cleantable.all_table["isp"][key]){
            vm.cleantable.isp.show[key].push({"name": provider, "checked": false})
          }
        }
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
      <a class="navbar-brand" href="#"><i class="fa fa-bars"></i> <!-- 这里使用了Font Awesome的bars图标 --> Dupin</a>
      <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav"
        aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav">
          <li class="nav-item">
            <a class="nav-link" href="#" @click="startWelcome">CleanTable</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#" @click="startVPNTable">VPN Table</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#" @click="startWeightTable">WeightTable</a>
          </li>
        </ul>
      </div>
    </nav>
    <div class="bd-example m-3"> <!--Local info-->
      <h1>Your current IP is: {{direct_data.local.ip}}.  Coordination: {{direct_data.local.coord}}.</h1>
      <p>Debugger: {{direct_data}} </p>
      <p> {{vpn_data}} </p>
      <p> {{modal_data}} </p>
      <p> Clean Table: </p>
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
              <l-map v-model:zoom="local_zoom" :center="direct_data.local.coord">
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
            <div class="d-flex flex-column align-items-center">
              <div>
                <button class="btn btn-primary" @click="vpn_detection">>VPN detect></button>
              </div>
              <div>
                Path selector:  
              </div>
              <div>
                <button class="btn btn-warning" :disabled="vpn_data.select.length <= 0" @click="redo()">↩</button>
                <button v-if="p_disconnect == false" class="btn btn-success" :disabled="vpn_data.select.length <= 0" @click="connect()">🔗</button>
                <button v-if="p_disconnect == true" class="btn btn-danger" :disabled="vpn_data.select.length <= 0" @click="disconnect()">🔗</button>
                <button class="btn btn-warning" :disabled="vpn_data.select.length <= 0" @click="path_clear()">↺</button>
              </div>
            </div>
          </div>
        </div>
        <div class="col">
          <div class="map">
            <div style="height:600px; width:800px">
              <l-map v-model:zoom="vpn_zoom" :center="direct_data.local.coord">
                <l-tile-layer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  layer-type="base"
                  name="OpenStreetMap"
                ></l-tile-layer>
                <l-marker v-for="(item, key, index) in vpn_data.node" :lat-lng="item.coord" :icon="getIcon(item.type)" @click="update_now(key)">
                  <l-tooltip :options="{ permanent: true, direction: 'bottom'}">
                    {{item.name}}
                  </l-tooltip>
                </l-marker>
                <template v-for="(item, key) in vpn_data.show_path">
                  <l-polyline v-for="(item2, key2) in item" :lat-lngs="item2.points" :color="item2.color">
                    <l-tooltip :options="{ permanent: true, interactive: true}" >
                      <span @click="showModal(key, key2, item2.data)" class="border border-primary rounded fs-6" :title="JSON.stringify(direct_data.line.summary,null, 4)">
                        {{item2.weight}}
                      </span>
                    </l-tooltip>
                  </l-polyline>
                </template>
              </l-map>
            </div>
          </div>
        </div>
      </div>
    </div>
    

    <!-- Info Modal -->
    <div class="modal fade" id="staticBackdrop" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1" aria-labelledby="staticBackdropLabel" aria-hidden="true">
      <div class="modal-dialog modal-xl modal-dialog-scrollable">
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
    <!--Info end-->
    
    <!-- Welcom Modal -->
    <div class="modal" id="welcom_modal" tabindex="-1">
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h1 class="modal-title">Welcome to Dupin Clean Connecter</h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <h5>First-time user?</h5><br>
            <h5>If so, please use our setup wizard to create your user config file.</h5><br>
            <h5>Already have a profile, you can choose "Ignore" botton.</h5>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Ignore</button>
            <button type="button" class="btn btn-primary" data-bs-dismiss="modal" @click="startWelcome">Start</button>
          </div>
        </div>
      </div>
    </div>
    <!-- Welcom end -->

    <!-- CleanTable -->
    <div class="modal fade" id="CleanTable" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1" aria-labelledby="staticBackdropLabel" aria-hidden="true">
      <div class="modal-dialog modal-xl modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h1 class="modal-title" id="staticBackdropLabel">
              Create Clean Table:
            </h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div class="row">
              <div class="col">
                <h5> Step1: Select ISP Table</h5>
              </div>
            </div>
            <div class="row">
              <div class="col-md-2">
                <div class="list-group">
                  <div class="list-group-item list-group-item-primary d-flex justify-content-between align-items-center">
                    <span>Contry:</span>
                    <div class="custom-control custom-checkbox">
                      <label class="custom-control-label" for="selectAll">►</label>
                    </div>
                  </div>
                </div>
                <div class="list-group custom-list-group">
                  <template v-if="cleantable.all_table !== null">
                    <button v-for="contry in Object.keys(cleantable.all_table['isp'])" @click="cleantable.isp.focus = contry" type="button" class="list-group-item list-group-item-action">
                      <input class="form-check-input me-1" type="checkbox" value="">
                      {{contry}}
                    </button>
                  </template>
                </div>
              </div>
              <div class="col-md-10">
                <div class="list-group">
                  <div class="list-group-item list-group-item-dark d-flex justify-content-between align-items-center">
                    <span>ISP Provider:</span>
                    <div class="custom-control custom-checkbox">
                      <input type="checkbox" class="custom-control-input" id="selectAll">
                      <label class="custom-control-label" for="selectAll">Select All</label>
                    </div>
                  </div>
                </div>
                <div class="list-group custom-list-group">
                  <template v-if="cleantable.isp.focus !== ''">                    
                    <label v-for="item in cleantable.isp.show[cleantable.isp.focus]" class="list-group-item">
                      <input class="form-check-input me-1" type="checkbox" :checked="item.checked">
                      {{item.name}}
                    </label>
                  </template>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            <button type="button" class="btn btn-warning" data-bs-dismiss="modal">Use Default config</button>
            <button type="button" class="btn btn-primary" data-bs-dismiss="modal" @click="startVPNTable">Next→Set VPN Table</button>
          </div>
        </div>
      </div>
    </div>
    <!--body end-->

    <!-- VPN Table -->
    <div class="modal fade" id="VPNTable" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1" aria-labelledby="staticBackdropLabel" aria-hidden="true">
      <div class="modal-dialog modal-xl modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h1 class="modal-title" id="staticBackdropLabel">
              VPN Table 
            </h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            test
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            <button type="button" class="btn btn-primary" data-bs-dismiss="modal" @click="startWeightTable">> Set VPN Table</button>
          </div>
        </div>
      </div>
    </div>
    <!-- VPN Table end-->

    <!-- WeightTable -->
    <div class="modal fade" id="WeightTable" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1" aria-labelledby="staticBackdropLabel" aria-hidden="true">
      <div class="modal-dialog modal-xl modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h1 class="modal-title" id="staticBackdropLabel">
              Weight Table 
            </h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            test
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
    <!--body end-->


  </div> 
  

  <!--loading-->
  <div id="dimScreen" v-if="loading">
    <div class="h-100 w-100 d-flex align-items-center justify-content-center">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
  </div>
  <!--loading end-->
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

.custom-list-group {
      max-height: 400px; /* 設定最大高度 */
      overflow-y: auto; /* 啟用垂直滾動條 */
    }
</style>