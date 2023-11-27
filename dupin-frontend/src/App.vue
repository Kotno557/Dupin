<script>
import "leaflet/dist/leaflet.css";
import { LMap, LTileLayer, LCircle, LMarker, LPopup, LTooltip, LPolyline } from "@vue-leaflet/vue-leaflet";
import moment from 'moment'
import L from "leaflet";
import axios from "axios";
import default_clean_table from '../../default-config-file/default_clean_table.json';
import history_table from '../../lib/dupin_python_lib/history.json'

import {Modal} from "bootstrap"
import { VueElement } from "vue";

let modal;
let welcon_modal
let clean_modal
let vpn_modal
let weight_modal
let history_modal

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
          "ip": "",
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
          "color": "blue"
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
        "select_weight": 0,
        "now": null,
        "shortest_info": {},
        "show_all": false
      },
      cleantable:{
        all_table: null,
        res:{
          "hdm":{
            "clean": {},
            "unclean": {}
          },
          "isp":{
            "clean": {},
            "unclean": {}
          }
        },
        isp:{
          focus: "",
          show: {}
        },
        hdm:{
          focus: "",
          show: {}
        }
      },
      vpntable:{
        res: {},
        input: {
          ip: null,
          name: null,
          path: null
        }
      },
      weighttable:{
        res: {
          "-1": 10000,
          "0": 10,
          "1": 5,
          "2": 3,
          "3": 0,
        }
      },
      input_vpn_table: undefined,
      local_zoom: 5,
      vpn_zoom: 5,
      loading: false,
      p_disconnect: false,

      default_clean_table,
      history_table
    };
  },
  methods: {
    getNowTime(){
      var date = new Date();
      var current_date = date.getFullYear()+"-"+(date.getMonth()+1)+"-"+ date.getDate();
      var current_time = date.getHours()+":"+date.getMinutes()+":"+ date.getSeconds();
      var date_time = current_date+" "+current_time;
      return date_time
    },
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
        this.vpn_data.path = dupin_vpn_result.data["res"]
        this.vpn_data.shortest_info = dupin_vpn_result.data["shortest_info"]

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
            var vpn_name = `VPN(${key})`
            this.vpn_data.node[key] = {
              "name": vpn_name,
              "ip": key,
              "coord": ipinfo_result.data["loc"].split(",").map(Number),
              "type": "enable",
              "show": true
            }
          }
        }
        console.log(this.vpn_data.path)
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
              "points": value2.draw_path, //show reflect
              // "points": [this.vpn_data.node[key].coord, this.vpn_data.node[key2].coord], show direct
              "color": findForth(value2.path_weight, max_weight, min_weight),
              "weight": value2.path_weight,
              "data": value2.info,
              "show": true
            }
          }
        }

        console.log("show_path", this.vpn_data.show_path)
      }
      catch(error) {
        console.log(error)
      }
      this.loading = false
      alert(`The VPN path scan has been completed.

      Please click on the grey VPN coordinates to determine the connection path.

      When you have confirm your selection, please press the green 🔗 button" to start the VPN-chaining connection.

      Onece you want to disconnect, press the red 🔗 button to termination the connection.

      If you don't see any coordinates on the VPN map, please check for error messages on the backend terminal.
      `)
    },
    async connect(){
      function delay(milliseconds){
        return new Promise(resolve => {
          setTimeout(resolve, milliseconds);
        });
      }
      this.loading = true

      let path_weight = 0
      let path = ['localhost'].concat(this.vpn_data.select)
      path.push(this.direct_data.target.url)
      for(let i = 0; i < path.length - 1; i+=1){
        path_weight += this.vpn_data.path[path[i]][path[i+1]].path_weight
      }
      this.vpn_data.select_weight = path_weight

      this.history_table[this.getNowTime()] = {
        "Start Local IP": this.direct_data.local.ip,
        "Target URL": this.direct_data.target.url,
        "Connect Path": this.vpn_data.select,
        "Weight_direct": this.direct_data.line.weight,
        "Weight_VPN": this.vpn_data.select_weight
      }

      try{
        await axios.post("http://localhost:8000/save_history", this.history_table)
        await axios.post(`http://localhost:8000/connect/?target_url=${this.direct_data.target.url}`, this.vpn_data.select)
      }
      catch(e){
        console.log("there is a catch of 500 Error")
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

          Weight of danger from:\n\n
          ${this.direct_data.line.weight} → ${this.vpn_data.select_weight}\n\n
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
    async history_connect(connect_path){
      this.vpn_data.select = connect_path

      // if(this.check_vpn_correct(connect_path) === false){
      //   console.log("connect_path", connect_path,"input_table", this.input_vpn_table)
      //   alert("The VPN selected path and VPN table not match.")
      //   return
      // }

      function delay(milliseconds){
        return new Promise(resolve => {
          setTimeout(resolve, milliseconds);
        });
      }
      this.loading = true

      // let path_weight = 0
      // let path = ['localhost'].concat(this.vpn_data.select)
      // path.push(this.direct_data.target.url)
      // for(let i = 0; i < path.length - 1; i+=1){
      //   path_weight += this.vpn_data.path[path[i]][path[i+1]].path_weight
      // }
      // this.vpn_data.select_weight = path_weight

      try{
        await axios.post(`http://localhost:8000/connect/?target_url=${this.direct_data.target.url}`, this.vpn_data.select)
      }
      catch(e){
        console.log("there is a catch of 500 Error")
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
    update_now (node_new) {
      console.log("click"+node_new)
      if (node_new === this.direct_data.target.url || node_new === "localhost" || this.vpn_data.node[node_new].type === "disable") {
        return
      }
      this.vpn_data.select.push(node_new)
      this.vpn_data.node[node_new].type = "disable"
      
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
    select_shortest_path(){
      this.path_clear()
      
      // let all path show = false
      let vm = this
      let ip_list = ['localhost'].concat(Object.keys(this.vpn_data.show_path['localhost']))
      ip_list.forEach(function (ip, i) {
        ip_list.forEach(function (ip2, j) {
          if(i < j){
            vm.vpn_data.show_path[ip][ip2]["show"] = false
          }
        })
      })

      // select shortest path in select array and let shortest path show = true
      for(let i = 0, j = 1; j < this.vpn_data.shortest_info["shortest_path"].length; i+=1, j+=1){
        this.update_now(this.vpn_data.shortest_info["shortest_path"][j])
        this.vpn_data.show_path[this.vpn_data.shortest_info["shortest_path"][i]][this.vpn_data.shortest_info["shortest_path"][j]]["show"] = true
      }

      if(this.vpn_data.shortest_info["shortest_path"].length <= 2){
        alert("The minimum weight path is a direct connection")
      }
    },
    upload_file(type, event){
      let formData = new FormData();
      formData.append("file", event.target.files[0])
      if (type === 2){
        this.upload_vpn_input_table(event)
      }
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
    startVPNTable(fromHome= true){
      let vm = this
      function download(fileName) {
          // 創建 Blob 對象
          var file = new Blob([JSON.stringify(vm.cleantable.res)], { type: 'application/json' });

          // 創建 Blob URL
          var blobUrl = window.URL.createObjectURL(file);

          // 創建新視窗，用於顯示 "Save As..." 對話框
          var a = document.createElement("a");
          a.style.display = "none";
          document.body.appendChild(a);

          // 設定新視窗的 URL 為 Blob URL
          a.href = blobUrl;
          a.download = fileName;

          // 觸發點擊事件以顯示 "Save As..." 對話框
          a.click();

          // 刪除創建的元素和 Blob URL，以避免內存洩漏
          document.body.removeChild(a);
          window.URL.revokeObjectURL(blobUrl);
      }
      if (fromHome === false) {
        download('UserCleanTable.json')
      }
      
      
      vpn_modal.show()
    },
    startWeightTable(fromHome = true){
      let vm = this
      function download(fileName) {
          // 創建 Blob 對象
          var file = new Blob([JSON.stringify(vm.vpntable.res)], { type: 'application/json' });

          // 創建 Blob URL
          var blobUrl = window.URL.createObjectURL(file);

          // 創建新視窗，用於顯示 "Save As..." 對話框
          var a = document.createElement("a");
          a.style.display = "none";
          document.body.appendChild(a);

          // 設定新視窗的 URL 為 Blob URL
          a.href = blobUrl;
          a.download = fileName;

          // 觸發點擊事件以顯示 "Save As..." 對話框
          a.click();

          // 刪除創建的元素和 Blob URL，以避免內存洩漏
          document.body.removeChild(a);
          window.URL.revokeObjectURL(blobUrl);
      }
      if (fromHome == false) {
        download('UserVPNTable.json')
      }
      weight_modal.show()
    },
    startHistoryTable(){
      if(this.input_vpn_table === undefined){
        alert("The history connection requires you to upload the VPN Table first.")
      }
      else{
        history_modal.show()
      }
    },
    weight_done(){
      let vm = this
      function download(fileName) {
          // 創建 Blob 對象
          var file = new Blob([JSON.stringify(vm.weighttable.res)], { type: 'application/json' });

          // 創建 Blob URL
          var blobUrl = window.URL.createObjectURL(file);

          // 創建新視窗，用於顯示 "Save As..." 對話框
          var a = document.createElement("a");
          a.style.display = "none";
          document.body.appendChild(a);

          // 設定新視窗的 URL 為 Blob URL
          a.href = blobUrl;
          a.download = fileName;

          // 觸發點擊事件以顯示 "Save As..." 對話框
          a.click();

          // 刪除創建的元素和 Blob URL，以避免內存洩漏
          document.body.removeChild(a);
          window.URL.revokeObjectURL(blobUrl);
      }
      download('UserWeightTable.json')
      vm.weighttable.res["-1"] = null
      vm.weighttable.res["0"] = null
      vm.weighttable.res["1"] = null
      vm.weighttable.res["2"] = null
      vm.weighttable.res["3"] = null
    },
    check_isp_alone(name, event, raw_value = null, raw_country = null){
      let value = (event !== undefined)? event.target.value : raw_value

      let country = raw_country !== null ? raw_country : this.cleantable.isp.focus

      this.cleantable.isp.show[country].list[name] = value
      
      if (value === "Don't care" || value === "Clean"){
        let danger_index = this.cleantable.res.isp.unclean[country].indexOf(name)
        if (danger_index !== -1){
          this.cleantable.res.isp.unclean[country].splice(danger_index, 1)
          this.cleantable.isp.show[country].danger_counter -= 1
        }
        if (value === "Clean" && this.cleantable.res.isp.clean[country].indexOf(name) === -1){
          this.cleantable.res.isp.clean[country].push(name)
          this.cleantable.isp.show[country].clean_counter += 1
        }
      }
      if (value === "Don't care" || value === "Danger"){
        let clean_index = this.cleantable.res.isp.clean[country].indexOf(name)
        if (clean_index !== -1){
          this.cleantable.res.isp.clean[country].splice(clean_index, 1)
          this.cleantable.isp.show[country].clean_counter -= 1
        }
        if (value === "Danger" && this.cleantable.res.isp.unclean[country].indexOf(name) === -1){
          this.cleantable.res.isp.unclean[country].push(name)
          this.cleantable.isp.show[country].danger_counter += 1
        }
      }        
    },
    check_isp_all(type){
      for (let provider of Object.keys(this.cleantable.isp.show[this.cleantable.isp.focus].list)) {
        this.check_isp_alone(provider, undefined, type)
      }
    },
    check_hdm_alone(name, event, raw_value = null, raw_category = null){
      let value = (event !== undefined)? event.target.value : raw_value
      let country = raw_category !== null ? raw_category : this.cleantable.hdm.focus
      this.cleantable.hdm.show[country].list[name] = value

      if (value === "Don't care" || value === "Clean"){
        let danger_index = this.cleantable.res.hdm.unclean[country].indexOf(name)
        if (danger_index !== -1){
          this.cleantable.res.hdm.unclean[country].splice(danger_index, 1)
          this.cleantable.hdm.show[country].danger_counter -= 1
        }
        if (value === "Clean" && this.cleantable.res.hdm.clean[country].indexOf(name) === -1){
          this.cleantable.res.hdm.clean[country].push(name)
          this.cleantable.hdm.show[country].clean_counter += 1
        }
      }
      if (value === "Don't care" || value === "Danger"){
        let clean_index = this.cleantable.res.hdm.clean[country].indexOf(name)
        if (clean_index !== -1){
          this.cleantable.res.hdm.clean[country].splice(clean_index, 1)
          this.cleantable.hdm.show[country].clean_counter -= 1
        }
        if (value === "Danger" && this.cleantable.res.hdm.unclean[country].indexOf(name) === -1){
          this.cleantable.res.hdm.unclean[country].push(name)
          this.cleantable.hdm.show[country].danger_counter += 1
        }
      }        
    },
    clean_table_import(name, value, type){
      let category_country = undefined
      for(let temp of Object.keys(this.cleantable[type].show)){
        for(let item of Object.keys(this.cleantable[type].show[temp].list)){
          if(item === name){
            category_country = temp
            break
          }
        }
        if(category_country !== undefined){
          break
        }
      }

      if(category_country !== undefined){
        if(type === "hdm"){
          this.check_hdm_alone(name, undefined, value, category_country)
        }
        else{
          this.check_isp_alone(name, undefined, value, category_country)
        }
      }
    },
    check_hdm_all(type){
      for (let provider of Object.keys(this.cleantable.hdm.show[this.cleantable.hdm.focus].list)) {
        this.check_hdm_alone(provider, undefined, type)
      }
    },
    add_vpn_node(){
      if (this.vpntable.input.ip === null || this.vpntable.input.name === null || this.vpntable.input.path === null){
        alert("Please ensure that the fields are filled in correctly")
      }
      else{
        this.vpntable.res[this.vpntable.input.ip] = {"name": this.vpntable.input.name, "ovpn_path": this.vpntable.input.path}
        this.vpntable.input.ip = null
        this.vpntable.input.name = null
        this.vpntable.input.path = null
      }
    },
    delet_vpn_node(ip){
      delete this.vpntable.res[ip]
    },
    vpn_path_all_select(){
      let vm = this
      let all_node = ['localhost'].concat(Object.keys(this.vpn_data.show_path['localhost']))
        all_node.forEach(function (ip, i){
          all_node.forEach(function (ip2, j){
            if (i < j){
              vm.vpn_data.show_path[ip][ip2]["show"] = !vm.vpn_data.show_all
            }
          })
        })
    },
    getDefaultCleanTable(){
      let vm = this
      function download(fileName) {
          // 創建 Blob 對象
          var file = new Blob([JSON.stringify(vm.default_clean_table)], { type: 'application/json' });
          // 創建 Blob URL
          var blobUrl = window.URL.createObjectURL(file);

          // 創建新視窗，用於顯示 "Save As..." 對話框
          var a = document.createElement("a");
          a.style.display = "none";
          document.body.appendChild(a);

          // 設定新視窗的 URL 為 Blob URL
          a.href = blobUrl;
          a.download = fileName;

          // 觸發點擊事件以顯示 "Save As..." 對話框
          a.click();

          // 刪除創建的元素和 Blob URL，以避免內存洩漏
          document.body.removeChild(a);
          window.URL.revokeObjectURL(blobUrl);
      }
      download('default_clean_table.json')
    },
    upload_clean_table(event){
      const file = event.target.files[0];
      if (file) {
        const reader = new FileReader();

        reader.onload = (e) => {
          try {
            // Parse the JSON data
            const parsedData = JSON.parse(e.target.result);
            console.log(parsedData)
            // Save the parsed data in the component's data
            // import hdm clean
            for(let type of Object.keys(parsedData["hdm"]["clean"])){
              for(let hdm of parsedData["hdm"]["clean"][type]){
                this.check_hdm_alone(hdm, undefined, "Clean", type)
              }
            }
            // import hdm danger
            for(let type of Object.keys(parsedData["hdm"]["unclean"])){
              for(let hdm of parsedData["hdm"]["unclean"][type]){
                this.check_hdm_alone(hdm, undefined, "Danger", type)
              }
            }
            // import isp clean
            for(let type of Object.keys(parsedData["isp"]["clean"])){
              for(let isp of parsedData["isp"]["clean"][type]){
                this.check_isp_alone(isp, undefined, "Clean", type)
              }
            }
            // import isp danger
            for(let type of Object.keys(parsedData["isp"]["unclean"])){
              for(let isp of parsedData["isp"]["unclean"][type]){
                this.check_isp_alone(isp, undefined, "Danger", type)
              }
            }
            
          } catch (error) {
            console.error('Error parsing JSON:', error);
            alert("Error JSON format:", error);
            this.jsonData = null;
          }
        };
        // Read the file as text
        reader.readAsText(file);
      }
    },
    upload_vpn_table(event){
      const file = event.target.files[0];
      if (file) {
        const reader = new FileReader();

        reader.onload = (e) => {
          try {
            // Parse the JSON data
            const parsedData = JSON.parse(e.target.result);
            console.log(parsedData)
            // Save the parsed data in the component's data
            // import hdm clean
            this.vpntable.res[this.vpntable.input.ip]
            for(let ip of Object.keys(parsedData)){
              this.vpntable.res[ip] = parsedData[ip]
            }
          } catch (error) {
            console.error('Error parsing JSON:', error);
            alert("Error JSON format:", error);
            this.jsonData = null;
          }
        };
        // Read the file as text
        reader.readAsText(file);
      }
    },
    upload_weight_table(event){
      const file = event.target.files[0];
      if (file) {
        const reader = new FileReader();

        reader.onload = (e) => {
          try {
            // Parse the JSON data
            const parsedData = JSON.parse(e.target.result);
            console.log(parsedData)
            // Save the parsed data in the component's data
            // import hdm clean
            this.vpntable.res[this.vpntable.input.ip]
            for(let level of Object.keys(parsedData)){
              this.weighttable.res[level] = parsedData[level]
            }
          } catch (error) {
            console.error('Error parsing JSON:', error);
            alert("Error JSON format:", error);
            this.jsonData = null;
          }
        };
        // Read the file as text
        reader.readAsText(file);
      }
    },
    upload_vpn_input_table(event){
      const file = event.target.files[0];
      if (file) {
        const reader = new FileReader();

        reader.onload = (e) => {
          try {
            // Parse the JSON data
            const parsedData = JSON.parse(e.target.result);
            console.log(parsedData)
            // Save the parsed data in the component's data
            // import hdm clean
            this.input_vpn_table = parsedData
          } catch (error) {
            console.error('Error parsing JSON:', error);
            alert("Error JSON format:", error);
            this.jsonData = null;
          }
        };
        // Read the file as text
        reader.readAsText(file);
      }
    },
    isInSameSubnet(ip1, ip2) {
      // 将IP地址转换为整数
      function ipToInteger(ip) {
        return ip.split('.').reduce(function (acc, octet, index, array) {
          return acc + parseInt(octet) * Math.pow(256, (array.length - index - 1));
        }, 0);
      }

      // 获取/24子网的掩码
      function getSubnetMask(ip) {
        return ipToInteger(ip) & ipToInteger('255.255.255.0');
      }

      // 将IP地址与/24子网的掩码进行比较
      return (ipToInteger(ip1) & getSubnetMask(ip1)) === (ipToInteger(ip2) & getSubnetMask(ip2));
    },
    check_vpn_correct(path_list){
      for(let vpn_ip of path_list){
        if(this.input_vpn_table === undefined || this.input_vpn_table[vpn_ip] === undefined){
          return true
        }
      }
      return false
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
    history_modal = new Modal(document.getElementById("HistoryTable"))
    welcon_modal.show()
    axios.get(`http://localhost:8000/brand_list`)
      .then(function (response) {
        vm.cleantable.all_table = response.data
        console.log(`[INFO] Get brand_list hdm size = ${vm.cleantable.all_table.hdm.length}, isp size = ${Object.keys(vm.cleantable.all_table.isp).length}`)
        console.log(vm.cleantable.all_table)
        for(let key of Object.keys(vm.cleantable.all_table["isp"])){
          vm.cleantable.res.isp.clean[key] = []
          vm.cleantable.res.isp.unclean[key] = []
          vm.cleantable.isp.show[key] = {list: {}, clean_counter: 0, danger_counter: 0}
          for(let provider of vm.cleantable.all_table["isp"][key]){
            vm.cleantable.isp.show[key].list[provider] = "Don't care"
          }
        }
        for(let key of Object.keys(vm.cleantable.all_table["hdm"])){
          vm.cleantable.res.hdm.clean[key] = []
          vm.cleantable.res.hdm.unclean[key] = []
          vm.cleantable.hdm.show[key] = {list: {}, clean_counter: 0, danger_counter: 0}
          for(let provider of vm.cleantable.all_table["hdm"][key]){
            vm.cleantable.hdm.show[key].list[provider] = "Don't care"
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
      <span class="navbar-brand" href="#"><i class="fa fa-bars"></i> <!-- 这里使用了Font Awesome的bars图标 --> Dupin</span>
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
          <li class="nav-item">
            <a class="nav-link" href="#" @click="startHistoryTable">HistoryTable</a>
          </li>
        </ul>
      </div>
    </nav>
    <div class="bd-example m-3"> <!--Local info-->
      <h1>Your current IP is: {{direct_data.local.ip}}, Coordination: {{direct_data.local.coord}}</h1>
      <!-- <p>Debugger: {{input_vpn_table}} </p> -->
      <!-- <p> {{vpn_data.path.}} </p> -->
      <!-- <p> {{modal_data}} </p> -->
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
          <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon3">http(s)://</span>
            <input v-model="direct_data.target.url" class="form-control" type="url" id="formFile" placeholder="google.com, aws.amazon.com, microsoft.com, and etc.">
            <span class="input-group-text" id="basic-addon3">/path/file</span>
          </div>
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
          <h5>▼ Direct Scan</h5>
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
                <button class="btn btn-primary" @click="vpn_detection" :disabled="direct_data.line.summary === null"> >VPN detect></button>
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
              <span>
                VPN chain select:
              </span>
              <span v-if="vpn_data.select.length == 0">
                None
              </span>
              <ul v-else class="list-group list-group-numbered" style="max-height: 150px; overflow-y: auto;">
                <li v-for="vpn in vpn_data.select" class="list-group-item py-0"><small>{{vpn}}</small></li>
              </ul>
            </div>
          </div>
        </div>
        <div class="col">
          <h5> ▼ VPN Scan</h5>
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
                  <template v-for="(item2, key2) in item">
                    <l-polyline v-if="item2.show" :lat-lngs="item2.points" :color="item2.color">
                      <l-tooltip :options="{ permanent: true, interactive: true}" >
                        <span @click="showModal(key, key2, item2.data)" class="border border-primary rounded fs-6" :title="JSON.stringify(direct_data.line.summary,null, 4)">
                          {{item2.weight}}
                        </span>
                      </l-tooltip>
                    </l-polyline>
                  </template>
                </template>
              </l-map>
            </div>
          </div>
          
          <div v-if="vpn_data.show_path['localhost'] !== undefined">
            <div class="d-flex">
              <span class="mx-2">
                (Danger
                <span style="color:#FF0000;">■</span>
                <span style="color:#B6B6B6;">■</span>
                <span style="color:#FFA500;">■</span>
                <span style="color:#FFFF00;">■</span>
                <span style="color:#008000;">■</span>
                Safe)
              </span>
              <span class="mx-2">
                <button @click="select_shortest_path" class="btn btn-info btn-sm py-0">>Select minimum weight path&lt; (weight:{{vpn_data.shortest_info["shortest_distance"]}})</button>
              </span>
            </div>

            <table class="table">
              <thead>
                <tr>
                  <th scope="col">
                    #
                    <input type="checkbox" v-model="vpn_data.show_all" @click="vpn_path_all_select" />
                  </th>
                  <th v-for="(ip, index) in ['localhost'].concat(Object.keys(vpn_data.show_path['localhost']))">{{ ip }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(ip, i) in ['localhost'].concat(Object.keys(vpn_data.show_path['localhost']))">
                  <th scope="row">{{ip}}</th>
                  <td v-for="(ip2, j) in ['localhost'].concat(Object.keys(vpn_data.show_path['localhost']))">
                    <span v-if="i == j">X</span>
                    <span v-else-if="i>j">
                      <!-- {{ ip2 }} {{ ip }} {{ vpn_data.show_path[ip2][ip]['show'] }} -->
                      <input type="checkbox" v-model="vpn_data.show_path[ip2][ip]['show']">
                      
                      <span :style="{'color': vpn_data.show_path[ip2][ip]['color']}"> ⬤</span>
                      {{vpn_data.show_path[ip2][ip]['weight']}}
                    </span>
                    <span v-else>
                      <!-- {{ ip }} {{ ip2 }} {{ vpn_data.show_path[ip][ip2]['show'] }} -->
                      <input type="checkbox" v-model="vpn_data.show_path[ip][ip2]['show']">
                      
                      <span :style="{'color': vpn_data.show_path[ip][ip2]['color']}"> ⬤</span>
                      {{vpn_data.show_path[ip][ip2]['weight']}}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
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
                  <th scope="col" v-for="head in ['IP', 'Level', 'Weight', 'Hardware', 'ISP', 'OS', 'Country']">
                    <strong>
                      {{head}}
                    </strong>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="key in Object.keys(modal_data.data)">
                  <td v-for="item in [key, modal_data.data[key].level, modal_data.data[key].single_weight, modal_data.data[key].hdm, modal_data.data[key].isp, modal_data.data[key].os, modal_data.data[key].country]">
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
            <div class="card p-4">
              <h5 class="mb-4">First-time user?</h5>
              <h5 class="mb-4">If so, please use our setup wizard to create your user config file.</h5>
              <h5>Already have it? You can press the "Ignore" button.</h5>
            </div>
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
            <!-- Step 1 ISP Selecter -->
            <div class="row">
              <div class="col">
                <h5> • Set ISP Trust Level</h5>
              </div>
            </div>
            <div class="row border p-1">
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
                    <button v-for="contry in Object.keys(cleantable.all_table['isp'])" @click="cleantable.isp.focus = contry" type="button" class="list-group-item list-group-item-action d-flex justify-content-between align-items-start">
                      <div>
                      {{contry}}
                      </div>
                      <div>
                        <span v-if="cleantable.isp.show[contry].clean_counter > 0" class="badge bg-success rounded-pill">{{ cleantable.isp.show[contry].clean_counter }}</span>
                        <span v-if="cleantable.isp.show[contry].danger_counter > 0" class="badge bg-danger rounded-pill">{{ cleantable.isp.show[contry].danger_counter }}</span>
                      </div>
                      </button>
                    
                  </template>
                </div>
              </div>
              <div class="col-md-10">
                <div class="list-group">
                  <div class="list-group-item list-group-item-dark d-flex justify-content-between align-items-center">
                    <span>ISP</span>
                    <div class="custom-control custom-checkbox">
                      
                      <template v-if="cleantable.isp.focus !== ''">
                        <label class="custom-control-label mx-2" for="selectAll">Select All ISP </label>
                        <div class="btn-group" role="group" aria-label="Basic mixed styles example">
                          <button @click="check_isp_all('Clean')" class="btn btn-success">Clean</button>
                          <button @click="check_isp_all('Don\'t care')" class="btn btn-light">Don't care</button>
                          <button @click="check_isp_all('Danger')" class="btn btn-danger">Danger</button>
                        </div>
                      </template>
                    </div>
                  </div>
                </div>
                <div class="list-group custom-list-group">
                  <template v-if="cleantable.isp.focus !== ''">                    
                    <label v-for="provider in Object.keys(cleantable.isp.show[cleantable.isp.focus].list) " class="list-group-item">
                      <select class="form-select-sm" v-bind:value="cleantable.isp.show[cleantable.isp.focus].list[provider]" @change="check_isp_alone(provider, $event)">
                        <option value="Clean" >Clean</option>
                        <option value="Danger" >Danger</option>
                        <option value="Don't care">Don't care</option>
                      </select>
                      {{provider}}
                    </label>
                  </template>
                </div>
              </div>
            </div>
            <!-- /Step 1 ISP Selecter -->

            <!-- Step 2 HDM Selecter -->
            <div class="row mt-4">
              <div class="col">
                <h5>• Step2: Select Hardware/OS Equipment Brand Table</h5>
              </div>
            </div>
            <div class="row border p-1">
              <div class="col-md-2">
                <div class="list-group">
                  <div class="list-group-item list-group-item-primary d-flex justify-content-between align-items-center">
                    <span>Category:</span>
                    <div class="custom-control custom-checkbox">
                      <label class="custom-control-label" for="selectAll">►</label>
                    </div>
                  </div>
                </div>
                <div class="list-group custom-list-group">
                  <template v-if="cleantable.all_table !== null">
                    <button v-for="category in Object.keys(cleantable.all_table['hdm'])" @click="cleantable.hdm.focus = category" type="button" class="list-group-item list-group-item-action d-flex justify-content-between align-items-start">
                      <div>
                      {{category}}
                      </div>
                      <div>
                        <span v-if="cleantable.hdm.show[category].clean_counter > 0" class="badge bg-success rounded-pill">{{ cleantable.hdm.show[category].clean_counter }}</span>
                        <span v-if="cleantable.hdm.show[category].danger_counter > 0" class="badge bg-danger rounded-pill">{{ cleantable.hdm.show[category].danger_counter }}</span>
                      </div>
                      </button>
                    
                  </template>
                </div>
              </div>
              <div class="col-md-10">
                <div class="list-group">
                  <div class="list-group-item list-group-item-dark d-flex justify-content-between align-items-center">
                    <span>Hardware/OS</span>
                    <div class="custom-control custom-checkbox">
                      
                      <template v-if="cleantable.hdm.focus !== ''">
                        <label class="custom-control-label mx-2" for="selectAll">Select All Hardware/OS Brand </label>
                        <div class="btn-group" role="group" aria-label="Basic mixed styles example">
                          <button @click="check_hdm_all('Clean')" class="btn btn-success">Clean</button>
                          <button @click="check_hdm_all('Don\'t care')" class="btn btn-light">Don't care</button>
                          <button @click="check_hdm_all('Danger')" class="btn btn-danger">Danger</button>
                        </div>
                      </template>
                    </div>
                  </div>
                </div>
                <div class="list-group custom-list-group">
                  <template v-if="cleantable.hdm.focus !== ''">                    
                    <label v-for="provider in Object.keys(cleantable.hdm.show[cleantable.hdm.focus].list) " class="list-group-item">
                      <select class="form-select-sm" v-bind:value="cleantable.hdm.show[cleantable.hdm.focus].list[provider]" @change="check_hdm_alone(provider, $event)">
                        <option value="Clean" >Clean</option>
                        <option value="Danger" >Danger</option>
                        <option value="Don't care">Don't care</option>
                      </select>
                      {{provider}}
                    </label>
                  </template>
                </div>
              </div>
            </div>
            <!-- <div class="row border p-1 mt-5">
              <p>
                <button class="btn btn-dark" type="button" data-bs-toggle="collapse" data-bs-target="#collapseExample" aria-expanded="false" aria-controls="collapseExample">
                  Debug Use: res Data ►
                </button>
              </p>
              <div class="collapse" id="collapseExample">
                <div class="card card-body">
                  {{ cleantable.res }}
                </div>
              </div>
              <p></p>
            </div> -->
            <!-- /Step 2 HDM Selecter -->
          </div>
          <div class="modal-footer">
            <div class="d-flex">
              <label class="input-group-text bg-info" for="inputGroupFile01">Edit From File:</label>
              <input type="file" class="form-control" id="inputGroupFile01" accept="application/JSON" @change="upload_clean_table($event)">
            </div>
            <button type="button" class="btn btn-warning" @click="getDefaultCleanTable">Get Default config</button>
            <button type="button" class="btn btn-primary" data-bs-dismiss="modal" @click="startVPNTable(false)">Save and Next→Set VPN Table</button>
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
              Create VPN Table 
            </h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <!-- Input Area -->
            <div>
              <form class="row g-3">
                <div class="col-md-12">
                  <h5>Add a VPN Node:</h5>
                </div>
                <div class="col-md-3">
                  <div class="input-group mb-3">
                    <span class="input-group-text" id="basic-addon3">IP</span>
                    <input v-model="vpntable.input.ip" class="form-control" placeholder="e.g. 223.138.2.119">
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="input-group mb-3">
                    <span class="input-group-text" id="basic-addon3">Name</span>
                    <input v-model="vpntable.input.name" class="form-control" placeholder="e.g. VPN_Japan">
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="input-group mb-3">
                    <span class="input-group-text" id="basic-addon3">ovpn file Path</span>
                    <input v-model="vpntable.input.path" class="form-control" placeholder="Input absolute path">
                  </div>
                </div>
                <div class="col-md-2">
                  <div class="input-group mb-3">
                    <button class="btn btn-primary" @click="add_vpn_node">Add VPN Node</button>
                  </div>
                </div>
              </form>
            </div>
            <!-- /Input Area -->
            <div class="mt-3">
              <h5>
                VPN Table:
              </h5>
              <table class="table">
                <thead>
                  <tr>
                    <th scope="col" class="col-md-1">IP</th>
                    <th scope="col" class="col-md-1">Name</th>
                    <th scope="col" class="col-md-3">oven file path</th>
                    <th scope="col" class="col-md-1">Operate</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="ip in Object.keys(vpntable.res)">
                    <th scope="row">{{ ip }}</th>
                    <td>{{ vpntable.res[ip]["name"] }}</td>
                    <td>{{ vpntable.res[ip]["ovpn_path"] }}</td>
                    <td>
                      <button class="btn btn-danger" @click="delet_vpn_node(ip)">Delete</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <!-- <div class="row border p-1 mt-5">
            <p>
              <button class="btn btn-dark" type="button" data-bs-toggle="collapse" data-bs-target="#collapseExample" aria-expanded="false" aria-controls="collapseExample">
                Debug Use: VPN res Table ►
              </button>
            </p>
            <div class="collapse" id="collapseExample">
              <div class="card card-body">
                <p>{{ vpntable.res }}</p>
                <p>{{ vpntable.input }}</p>
              </div>
            </div>
            <p></p>
          </div> -->
          <div class="modal-footer">
            <div class="d-flex">
              <label class="input-group-text bg-info" for="inputGroupFile02">Edit From File:</label>
              <input type="file" class="form-control" id="inputGroupFile02" accept="application/JSON" @change="upload_vpn_table($event)">
            </div>
            <button type="button" class="btn btn-primary" data-bs-dismiss="modal" @click="startWeightTable(false)">> Set VPN Table</button>
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
              Create Weight Table:
            </h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <h2 class="my-3">
              Input weights:
            </h2>
            <h5 class="my-4">
              Please note that weights should be input as positive integers, including 0.<br>
              Lower weights indicate higher safety.
            </h5>
            <span class="text-danger mt-5">(If you have no clue about this, please use the default values directly.)</span>
            
            <form class="row g-3">
              <div class="col-md-6">
                <div class="input-group input-group-lg">
                  <span class="input-group-text bg-danger">DANGER</span>
                  <input v-model="weighttable.res['-1']" type="number" class="form-control" aria-label="Sizing example input" aria-describedby="inputGroup-sizing-lg">
                </div>
              </div>
              <div class="col-md-6">
                <div class="input-group input-group-lg">
                  <span class="input-group-text bg-secondary">UNKNOWN</span>
                  <input v-model="weighttable.res['0']" type="number" class="form-control" aria-label="Sizing example input" aria-describedby="inputGroup-sizing-lg">
                </div>
              </div>
              <div class="col-md-6">
                <div class="input-group input-group-lg">
                  <span class="input-group-text bg-warning">LOW</span>
                  <input v-model="weighttable.res['1']" type="number" class="form-control" aria-label="Sizing example input" aria-describedby="inputGroup-sizing-lg">
                </div>
              </div>
              <div class="col-md-6">
                <div class="input-group input-group-lg">
                  <span class="input-group-text bg-primary" >PASSABLE</span>
                  <input v-model="weighttable.res['2']" type="number" class="form-control" aria-label="Sizing example input" aria-describedby="inputGroup-sizing-lg">
                </div>
              </div>
              <div class="col-md-6">
                <div class="input-group input-group-lg">
                  <span class="input-group-text bg-success" >SAFE</span>
                  <input v-model="weighttable.res['3']" type="number" class="form-control" aria-label="Sizing example input" aria-describedby="inputGroup-sizing-lg">
                </div>
              </div>
            </form>
          </div>
          <!-- <div class="row border p-1 mt-5">
            <p>
              <button class="btn btn-dark" type="button" data-bs-toggle="collapse" data-bs-target="#collapseExample" aria-expanded="false" aria-controls="collapseExample">
                Debug Use: Weight res Table ►
              </button>
            </p>
            <div class="collapse" id="collapseExample">
              <div class="card card-body">
                <p>{{ weighttable.res }}</p>
              </div>
            </div>
          </div> -->

          <div class="modal-footer">
            <div class="d-flex">
              <label class="input-group-text bg-info" for="inputGroupFile03">Edit From File:</label>
              <input type="file" class="form-control" id="inputGroupFile03" accept="application/JSON" @change="upload_weight_table($event)">
            </div>
            <button type="button" class="btn btn-primary" data-bs-dismiss="modal" @click="weight_done(fromHome=false)">Save and Done</button>
          </div>
        </div>
      </div>
    </div>

    <!-- history -->
    <div class="modal fade" id="HistoryTable" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1" aria-labelledby="staticBackdropLabel" aria-hidden="true">
      <div class="modal-dialog modal-xl modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h1 class="modal-title" id="staticBackdropLabel">
              Connect History:
            </h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <ul class="list-unstyled">
              <h2 class="my-3">
                History connection records:
              </h2>
              <li>- This table records past connection history. If the "operate" button is disabled, it indicates that the connection node does not match the current input VPN Table.</li>
              <li>- When the IP is displayed in green text, it signifies that the IP is in the same network segment as the current IP (/24). In such cases, a new connection may resemble the scenario recorded in this history.
                <ul>
                  <li>*To enhance security, it is not recommended to use historical connections from different network segments to avoid increasing the exposure risk.</li>
                </ul>
              </li>
            </ul>
            <table class="table">
              <thead>
                <tr>
                  <th scope="col">Time</th>
                  <th scope="col">Start Local IP</th>
                  <th scope="col">Target IP</th>
                  <th scope="col">Connect Path</th>
                  <th scope="col">Weight Direct</th>
                  <th scope="col">Weight VPN Use</th>
                  <th scope="col">Operate</th>
                </tr>
              </thead>
              <tbody>
                <template v-if="Object.keys(history_table).length > 0">
                  <tr v-for="time in Object.keys(history_table)">
                    <th scope="row">{{ time }}</th>
                    <td :class="isInSameSubnet(direct_data.local.ip, history_table[time]['Start Local IP']) ? ['text-success'] :[]">{{ history_table[time]["Start Local IP"] }}</td>
                    <td>{{ history_table[time]["Target URL"] }}</td>
                    <td>{{ history_table[time]["Connect Path"] }}</td>
                    <td>{{ history_table[time]["Weight_direct"] }}</td>
                    <td>{{ history_table[time]["Weight_VPN"] }}</td>
                    <td>
                      <button v-if="p_disconnect == false" class="btn btn-success btn-sm py-0" @click="history_connect(history_table[time]['Connect Path'])" :disabled="check_vpn_correct(history_table[time]['Connect Path'])">🔗</button>
                      <button v-if="p_disconnect == true" class="btn btn-danger btn-sm py-0" :disabled="vpn_data.select.length <= 0" @click="disconnect()">🔗</button>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!--/ history -->
  </div>  
  <!--body end-->
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
    z-index: 9999;
}

.custom-list-group {
      max-height: 400px; /* 設定最大高度 */
      overflow-y: auto; /* 啟用垂直滾動條 */
    }
</style>