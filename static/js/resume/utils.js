/* ==========================================
   UTILITIES
========================================== */

function debounce(callback, delay = 800){

    let timer;

    return function(...args){

        clearTimeout(timer);

        timer = setTimeout(() => {

            callback.apply(this,args);

        },delay);

    };

}

function deepClone(object){

    return JSON.parse(

        JSON.stringify(object)

    );

}

function isEmpty(value){

    return value === null ||

           value === undefined ||

           value === "";

}