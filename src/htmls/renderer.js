"use strict";


function CodeViewer (){

    this.colorTheme = {
        "background-left": "rgb(150, 150, 150)",
        "background-right": "rgb(255, 255, 255)",
        "highlight": "rgb(254, 251, 215)",

        // "": "rgb(, , )",
    }

    this.render = function (paragraph, DIVID){

        let thisLib = this;

        let container = document.getElementById(DIVID);
        console.log(paragraph)
        console.log(DIVID)
        console.log(container)
        container.innerHTML = "";
        container.style.overflowX = "scroll";
        container.style.position = "relative";

        let lines = paragraph.split("\n");

        let tableEle = document.createElement("table");
        tableEle.style = "width: 100%; font-family: monospace; border-radius: 10px; padding: 10px; background-color: " + this.colorTheme["background-right"];

        for (let linenum in lines){
            let line = lines[linenum];

            let code_ele = document.createElement("tr");


            let br = "";
            if (line.trim() === ""){
                br = "<br>";
            }

            line = line.replaceAll(" ", "&nbsp");


            code_ele.innerHTML += "<td style='min-width: 40px; width: 40px; text-align: right; user-select: none; border-right: black solid 2px; padding-right: 2px;'>"+linenum.toString()+"</td><td style=''>"+line+"</td>" + br;

            code_ele.onmouseover = function (){

                let tds = this.getElementsByTagName("td");
                let td0 = tds[0];
                let td1 = tds[1];

                td0.style.fontWeight = "bold"
                td1.style.backgroundColor = thisLib.colorTheme.highlight

            }

            code_ele.onmouseleave = function (){

                let tds = this.getElementsByTagName("td");
                let td0 = tds[0];
                let td1 = tds[1];

                td0.style.fontWeight = "normal"
                td1.style.backgroundColor = thisLib.colorTheme["background-right"]
            }


            tableEle.appendChild(code_ele)
        }

        let shadowEle = document.createElement("div");
        shadowEle.style = "position: absolute; width: 57px; height: 100%; top: 0; left: 0; opacity: 0.5; border-radius: 10px 0 0 10px; background-color: " + this.colorTheme["background-left"];

        let copyEle = document.createElement("div");
        copyEle.innerHTML = "<svg xmlns=\"http://www.w3.org/2000/svg\" width=30px height=30px fill=\"currentColor\" class=\"bi bi-files\" viewBox=\"0 0 16 16\">\n" +
            "  <path d=\"M13 0H6a2 2 0 0 0-2 2 2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h7a2 2 0 0 0 2-2 2 2 0 0 0 2-2V2a2 2 0 0 0-2-2zm0 13V4a2 2 0 0 0-2-2H5a1 1 0 0 1 1-1h7a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1zM3 4a1 1 0 0 1 1-1h7a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4z\"/>\n" +
            "</svg>";
        copyEle.style = "position: absolute; top: 15px; right: 15px; background-color: white; border: lightgrey solid 1px; cursor: pointer; padding-top: 3px; padding-right: 2px; ";
        copyEle.onclick = function (){
            var copyText = document.createElement("textarea");
            copyText.value = paragraph;

            document.getElementsByTagName("body")[0].appendChild(copyText);

            copyText.select();
            copyText.setSelectionRange(0, 99999);

            document.execCommand("copy");
            copyText.remove()
        }


        container.appendChild(tableEle)
        container.appendChild(shadowEle)
        container.appendChild(copyEle)

    }

    return {
        "colorTheme": this.colorTheme,
        "render": this.render,
        // "": this.,
    }
}


"use strict";

function JSONViewer (){
    this.tmp = "";

    this.unicodeCollapse = "▸";
    this.unicodeExpand   = "▾";
    this.defaultExpandDepth = 2;

    this.colorTheme = {
        "key": "rgb(0, 116, 232)",
        "object": "rgb(0, 116, 232)",
        "string": "rgb(221, 0, 169)",
        "number": "rgb(5, 139, 0)",
        "other": "rgb(5, 139, 0)",
        "background": "rgb(255, 255, 255)",
        "highlight": "rgb(240, 249, 254)",

        // "": "rgb(, , )",
    };

    this.objectWalk = function (obj){

        let res = [];

        let toDiscover = [];
        for (let k of Object.keys(obj).sort().reverse()){
            toDiscover.push([k, obj, 0])
        }

        while (toDiscover.length > 0){
            let pair = toDiscover.pop();

            let parent = pair[1];
            let k = pair[0];
            let v = parent[k];
            let depth = pair[2]

            if (typeof v === "object"){
                for (let kk of Object.keys(v).sort().reverse()){
                    toDiscover.push([kk, v, depth+1])
                }
            }

            res.push([k, v, depth])
        }

        return res
    }

    this.renderrow = function (key, value, depth) {

        let thisLib = this;

        let result = document.createElement("tr");

        let collapse = false;
        let collapsible = false;
        let rowDataType = "object";
        let objectLength = 0;
        let hide = false

        if (depth >= this.defaultExpandDepth) {
            collapse = true;
        }
        if (depth > this.defaultExpandDepth) {
            hide = true;
            collapse = false;
        }

        let td1 = document.createElement("td")
        td1.style = "cursor: pointer;"
        td1.style.color = this.colorTheme.key



        let td2 = document.createElement("td")
        td2.style = "";

        if (typeof value === "object"){
            objectLength = Object.keys(value).length;

            let bracket1 = "{", bracket2 = "}";

            if (Array.isArray(value)){
                rowDataType = "array";
                bracket1 = "[";
                bracket2 = "]";
            }

            if (objectLength > 0) {
                collapsible = true;
                td2.innerHTML = bracket1 + "..." + bracket2;
            } else {
                td2.innerHTML = bracket1 + " " + bracket2;
            }

            if (!collapse && collapsible){
                td2.innerHTML = "";
            }


            td2.style.color = this.colorTheme.object
        }
        else {
            rowDataType = "other"
            td2.innerHTML = value;

            if (typeof value === "string") {
                td2.innerHTML = "\""+td2.innerHTML+"\"";
                td2.style.color = this.colorTheme.string
            }
            else if (typeof value === "number") {
                td2.style.color = this.colorTheme.number
            }
            else {
                td2.style.color = this.colorTheme.other
            }
        }

        let arrow = "";
        if (collapsible && collapse){
            arrow = this.unicodeCollapse;
        }

        if (collapsible && !collapse){
            arrow = this.unicodeExpand;
        }


        let arrowele = "<span style='color: grey; position: absolute; text-align: center; '>"+ "&nbsp".repeat(depth * 4) + arrow + "</span>"
        td1.innerHTML = arrowele + "&nbsp".repeat(depth * 4 + 4) + key + ":&nbsp";


        result.setAttribute("data-depth", depth.toString())
        result.setAttribute("data-dataType", rowDataType)
        result.setAttribute("data-collapse", collapse.toString())
        result.setAttribute("data-collapsible", collapsible.toString())

        result.style = "";
        if (hide){
            result.style.display = "none";
        }


        result.onmouseover = function () {
            this.style.backgroundColor = thisLib.colorTheme.highlight;
        }
        result.onmouseleave = function () {
            this.style.backgroundColor = thisLib.colorTheme.background;
        }

        td1.onclick = function (){
            let parent = this.parentNode;

            let thisdepth = parseInt(parent.getAttribute("data-depth"));
            let thisdatatype = result.getAttribute("data-dataType");
            let thiscollapse = parent.getAttribute("data-collapse") === "true";
            let thiscollapsible = parent.getAttribute("data-collapsible") === "true";


            let displayStyle = "none";
            if (thiscollapse) {
                displayStyle = "";
            }


            if (thiscollapsible){

                let abbr = "{...}"
                if (thisdatatype === "array"){
                    abbr = "[...]"
                }

                let td0 = parent.getElementsByTagName("td")[0];
                if (thiscollapse){
                    abbr = "";
                    td0.innerHTML = td0.innerHTML.replace(thisLib.unicodeCollapse, thisLib.unicodeExpand)
                } else {
                    td0.innerHTML = td0.innerHTML.replace(thisLib.unicodeExpand, thisLib.unicodeCollapse)
                }

                parent.getElementsByTagName("td")[1].innerText = abbr;

                parent.setAttribute("data-collapse", (!thiscollapse).toString())

                let allTR = parent.parentNode.getElementsByTagName("tr");
                let start = false
                for (let tr0 of allTR){

                    if (tr0 == parent){
                        start = true;
                        continue
                    }
                    if (!start) {
                        continue
                    }

                    let nextdepth = parseInt(tr0.getAttribute("data-depth"));
                    if (nextdepth > thisdepth){
                        tr0.style.display = displayStyle;
                        tr0.setAttribute("data-collapse", "false")
                    } else {
                        break
                    }
                    let td0 = tr0.getElementsByTagName("td")[0];
                    td0.innerHTML = td0.innerHTML.replace(thisLib.unicodeCollapse, thisLib.unicodeExpand);


                }
            }
        }

        result.appendChild(td1);
        result.appendChild(td2);

        return result
    }

    this.render = function (data, divid){
        let container = document.getElementById(divid);
        container.innerHTML = "";

        let result = document.createElement("table");
        result.style = "width: 100%; border-radius: 10px; background-color: " + this.colorTheme.background;
        for (let line of this.objectWalk(data)){

            let key = line[0];
            let value = line[1];
            let depth = line[2];

            let tr = this.renderrow(key, value, depth)
            result.appendChild(tr);
        }


        container.appendChild(result)
    }

    return {
        "render": this.render,
        "renderrow": this.renderrow,
        "objectWalk": this.objectWalk,
        "colorTheme": this.colorTheme,
        "unicodeCollapse": this.unicodeCollapse,
        "unicodeExpand": this.unicodeExpand,
        "defaultExpandDepth": this.defaultExpandDepth,
    }

}



