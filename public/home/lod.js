var K$="srgb";class O6{addEventListener(J,$){if(this._listeners===void 0)this._listeners={};let Q=this._listeners;if(Q[J]===void 0)Q[J]=[];if(Q[J].indexOf($)===-1)Q[J].push($)}hasEventListener(J,$){if(this._listeners===void 0)return!1;let Q=this._listeners;return Q[J]!==void 0&&Q[J].indexOf($)!==-1}removeEventListener(J,$){if(this._listeners===void 0)return;let Z=this._listeners[J];if(Z!==void 0){let W=Z.indexOf($);if(W!==-1)Z.splice(W,1)}}dispatchEvent(J){if(this._listeners===void 0)return;let Q=this._listeners[J.type];if(Q!==void 0){J.target=this;let Z=Q.slice(0);for(let W=0,Y=Z.length;W<Y;W++)Z[W].call(this,J);J.target=null}}}var F0=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"];var l7=Math.PI/180,v8=180/Math.PI;function H6(){let J=Math.random()*4294967295|0,$=Math.random()*4294967295|0,Q=Math.random()*4294967295|0,Z=Math.random()*4294967295|0;return(F0[J&255]+F0[J>>8&255]+F0[J>>16&255]+F0[J>>24&255]+"-"+F0[$&255]+F0[$>>8&255]+"-"+F0[$>>16&15|64]+F0[$>>24&255]+"-"+F0[Q&63|128]+F0[Q>>8&255]+"-"+F0[Q>>16&255]+F0[Q>>24&255]+F0[Z&255]+F0[Z>>8&255]+F0[Z>>16&255]+F0[Z>>24&255]).toLowerCase()}function z0(J,$,Q){return Math.max($,Math.min(Q,J))}function a$(J,$){return(J%$+$)%$}function Z8(J,$,Q){return(1-Q)*J+Q*$}function x0(J,$){switch($.constructor){case Float32Array:return J;case Uint32Array:return J/4294967295;case Uint16Array:return J/65535;case Uint8Array:return J/255;case Int32Array:return Math.max(J/2147483647,-1);case Int16Array:return Math.max(J/32767,-1);case Int8Array:return Math.max(J/127,-1);default:throw Error("Invalid component type.")}}function aJ(J,$){switch($.constructor){case Float32Array:return J;case Uint32Array:return Math.round(J*4294967295);case Uint16Array:return Math.round(J*65535);case Uint8Array:return Math.round(J*255);case Int32Array:return Math.round(J*2147483647);case Int16Array:return Math.round(J*32767);case Int8Array:return Math.round(J*127);default:throw Error("Invalid component type.")}}class uJ{constructor(J=0,$=0){uJ.prototype.isVector2=!0,this.x=J,this.y=$}get width(){return this.x}set width(J){this.x=J}get height(){return this.y}set height(J){this.y=J}set(J,$){return this.x=J,this.y=$,this}setScalar(J){return this.x=J,this.y=J,this}setX(J){return this.x=J,this}setY(J){return this.y=J,this}setComponent(J,$){switch(J){case 0:this.x=$;break;case 1:this.y=$;break;default:throw Error("index is out of range: "+J)}return this}getComponent(J){switch(J){case 0:return this.x;case 1:return this.y;default:throw Error("index is out of range: "+J)}}clone(){return new this.constructor(this.x,this.y)}copy(J){return this.x=J.x,this.y=J.y,this}add(J){return this.x+=J.x,this.y+=J.y,this}addScalar(J){return this.x+=J,this.y+=J,this}addVectors(J,$){return this.x=J.x+$.x,this.y=J.y+$.y,this}addScaledVector(J,$){return this.x+=J.x*$,this.y+=J.y*$,this}sub(J){return this.x-=J.x,this.y-=J.y,this}subScalar(J){return this.x-=J,this.y-=J,this}subVectors(J,$){return this.x=J.x-$.x,this.y=J.y-$.y,this}multiply(J){return this.x*=J.x,this.y*=J.y,this}multiplyScalar(J){return this.x*=J,this.y*=J,this}divide(J){return this.x/=J.x,this.y/=J.y,this}divideScalar(J){return this.multiplyScalar(1/J)}applyMatrix3(J){let $=this.x,Q=this.y,Z=J.elements;return this.x=Z[0]*$+Z[3]*Q+Z[6],this.y=Z[1]*$+Z[4]*Q+Z[7],this}min(J){return this.x=Math.min(this.x,J.x),this.y=Math.min(this.y,J.y),this}max(J){return this.x=Math.max(this.x,J.x),this.y=Math.max(this.y,J.y),this}clamp(J,$){return this.x=Math.max(J.x,Math.min($.x,this.x)),this.y=Math.max(J.y,Math.min($.y,this.y)),this}clampScalar(J,$){return this.x=Math.max(J,Math.min($,this.x)),this.y=Math.max(J,Math.min($,this.y)),this}clampLength(J,$){let Q=this.length();return this.divideScalar(Q||1).multiplyScalar(Math.max(J,Math.min($,Q)))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(J){return this.x*J.x+this.y*J.y}cross(J){return this.x*J.y-this.y*J.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(J){let $=Math.sqrt(this.lengthSq()*J.lengthSq());if($===0)return Math.PI/2;let Q=this.dot(J)/$;return Math.acos(z0(Q,-1,1))}distanceTo(J){return Math.sqrt(this.distanceToSquared(J))}distanceToSquared(J){let $=this.x-J.x,Q=this.y-J.y;return $*$+Q*Q}manhattanDistanceTo(J){return Math.abs(this.x-J.x)+Math.abs(this.y-J.y)}setLength(J){return this.normalize().multiplyScalar(J)}lerp(J,$){return this.x+=(J.x-this.x)*$,this.y+=(J.y-this.y)*$,this}lerpVectors(J,$,Q){return this.x=J.x+($.x-J.x)*Q,this.y=J.y+($.y-J.y)*Q,this}equals(J){return J.x===this.x&&J.y===this.y}fromArray(J,$=0){return this.x=J[$],this.y=J[$+1],this}toArray(J=[],$=0){return J[$]=this.x,J[$+1]=this.y,J}fromBufferAttribute(J,$){return this.x=J.getX($),this.y=J.getY($),this}rotateAround(J,$){let Q=Math.cos($),Z=Math.sin($),W=this.x-J.x,Y=this.y-J.y;return this.x=W*Q-Y*Z+J.x,this.y=W*Z+Y*Q+J.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}}class jJ{constructor(J,$,Q,Z,W,Y,X,H,K){if(jJ.prototype.isMatrix3=!0,this.elements=[1,0,0,0,1,0,0,0,1],J!==void 0)this.set(J,$,Q,Z,W,Y,X,H,K)}set(J,$,Q,Z,W,Y,X,H,K){let G=this.elements;return G[0]=J,G[1]=Z,G[2]=X,G[3]=$,G[4]=W,G[5]=H,G[6]=Q,G[7]=Y,G[8]=K,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(J){let $=this.elements,Q=J.elements;return $[0]=Q[0],$[1]=Q[1],$[2]=Q[2],$[3]=Q[3],$[4]=Q[4],$[5]=Q[5],$[6]=Q[6],$[7]=Q[7],$[8]=Q[8],this}extractBasis(J,$,Q){return J.setFromMatrix3Column(this,0),$.setFromMatrix3Column(this,1),Q.setFromMatrix3Column(this,2),this}setFromMatrix4(J){let $=J.elements;return this.set($[0],$[4],$[8],$[1],$[5],$[9],$[2],$[6],$[10]),this}multiply(J){return this.multiplyMatrices(this,J)}premultiply(J){return this.multiplyMatrices(J,this)}multiplyMatrices(J,$){let Q=J.elements,Z=$.elements,W=this.elements,Y=Q[0],X=Q[3],H=Q[6],K=Q[1],G=Q[4],E=Q[7],U=Q[2],q=Q[5],D=Q[8],N=Z[0],O=Z[3],V=Z[6],F=Z[1],A=Z[4],z=Z[7],_=Z[2],b=Z[5],L=Z[8];return W[0]=Y*N+X*F+H*_,W[3]=Y*O+X*A+H*b,W[6]=Y*V+X*z+H*L,W[1]=K*N+G*F+E*_,W[4]=K*O+G*A+E*b,W[7]=K*V+G*z+E*L,W[2]=U*N+q*F+D*_,W[5]=U*O+q*A+D*b,W[8]=U*V+q*z+D*L,this}multiplyScalar(J){let $=this.elements;return $[0]*=J,$[3]*=J,$[6]*=J,$[1]*=J,$[4]*=J,$[7]*=J,$[2]*=J,$[5]*=J,$[8]*=J,this}determinant(){let J=this.elements,$=J[0],Q=J[1],Z=J[2],W=J[3],Y=J[4],X=J[5],H=J[6],K=J[7],G=J[8];return $*Y*G-$*X*K-Q*W*G+Q*X*H+Z*W*K-Z*Y*H}invert(){let J=this.elements,$=J[0],Q=J[1],Z=J[2],W=J[3],Y=J[4],X=J[5],H=J[6],K=J[7],G=J[8],E=G*Y-X*K,U=X*H-G*W,q=K*W-Y*H,D=$*E+Q*U+Z*q;if(D===0)return this.set(0,0,0,0,0,0,0,0,0);let N=1/D;return J[0]=E*N,J[1]=(Z*K-G*Q)*N,J[2]=(X*Q-Z*Y)*N,J[3]=U*N,J[4]=(G*$-Z*H)*N,J[5]=(Z*W-X*$)*N,J[6]=q*N,J[7]=(Q*H-K*$)*N,J[8]=(Y*$-Q*W)*N,this}transpose(){let J,$=this.elements;return J=$[1],$[1]=$[3],$[3]=J,J=$[2],$[2]=$[6],$[6]=J,J=$[5],$[5]=$[7],$[7]=J,this}getNormalMatrix(J){return this.setFromMatrix4(J).invert().transpose()}transposeIntoArray(J){let $=this.elements;return J[0]=$[0],J[1]=$[3],J[2]=$[6],J[3]=$[1],J[4]=$[4],J[5]=$[7],J[6]=$[2],J[7]=$[5],J[8]=$[8],this}setUvTransform(J,$,Q,Z,W,Y,X){let H=Math.cos(W),K=Math.sin(W);return this.set(Q*H,Q*K,-Q*(H*Y+K*X)+Y+J,-Z*K,Z*H,-Z*(-K*Y+H*X)+X+$,0,0,1),this}scale(J,$){return this.premultiply(W8.makeScale(J,$)),this}rotate(J){return this.premultiply(W8.makeRotation(-J)),this}translate(J,$){return this.premultiply(W8.makeTranslation(J,$)),this}makeTranslation(J,$){if(J.isVector2)this.set(1,0,J.x,0,1,J.y,0,0,1);else this.set(1,0,J,0,1,$,0,0,1);return this}makeRotation(J){let $=Math.cos(J),Q=Math.sin(J);return this.set($,-Q,0,Q,$,0,0,0,1),this}makeScale(J,$){return this.set(J,0,0,0,$,0,0,0,1),this}equals(J){let $=this.elements,Q=J.elements;for(let Z=0;Z<9;Z++)if($[Z]!==Q[Z])return!1;return!0}fromArray(J,$=0){for(let Q=0;Q<9;Q++)this.elements[Q]=J[Q+$];return this}toArray(J=[],$=0){let Q=this.elements;return J[$]=Q[0],J[$+1]=Q[1],J[$+2]=Q[2],J[$+3]=Q[3],J[$+4]=Q[4],J[$+5]=Q[5],J[$+6]=Q[6],J[$+7]=Q[7],J[$+8]=Q[8],J}clone(){return new this.constructor().fromArray(this.elements)}}var W8=new jJ;function G$(J){for(let $=J.length-1;$>=0;--$)if(J[$]>=65535)return!0;return!1}function c7(J){return document.createElementNS("http://www.w3.org/1999/xhtml",J)}function r$(){let J=c7("canvas");return J.style.display="block",J}var U9={};function Z7(J){if(J in U9)return;U9[J]=!0,console.warn(J)}function t$(J,$,Q){return new Promise(function(Z,W){function Y(){switch(J.clientWaitSync($,J.SYNC_FLUSH_COMMANDS_BIT,0)){case J.WAIT_FAILED:W();break;case J.TIMEOUT_EXPIRED:setTimeout(Y,Q);break;default:Z()}}setTimeout(Y,Q)})}function e$(J){let $=J.elements;$[2]=0.5*$[2]+0.5*$[3],$[6]=0.5*$[6]+0.5*$[7],$[10]=0.5*$[10]+0.5*$[11],$[14]=0.5*$[14]+0.5*$[15]}function J5(J){let $=J.elements;if($[11]===-1)$[10]=-$[10]-1,$[14]=-$[14];else $[10]=-$[10],$[14]=-$[14]+1}var dJ={enabled:!0,workingColorSpace:"srgb-linear",spaces:{},convert:function(J,$,Q){if(this.enabled===!1||$===Q||!$||!Q)return J;if(this.spaces[$].transfer==="srgb")J.r=i0(J.r),J.g=i0(J.g),J.b=i0(J.b);if(this.spaces[$].primaries!==this.spaces[Q].primaries)J.applyMatrix3(this.spaces[$].toXYZ),J.applyMatrix3(this.spaces[Q].fromXYZ);if(this.spaces[Q].transfer==="srgb")J.r=g6(J.r),J.g=g6(J.g),J.b=g6(J.b);return J},fromWorkingColorSpace:function(J,$){return this.convert(J,this.workingColorSpace,$)},toWorkingColorSpace:function(J,$){return this.convert(J,$,this.workingColorSpace)},getPrimaries:function(J){return this.spaces[J].primaries},getTransfer:function(J){if(J==="")return"linear";return this.spaces[J].transfer},getLuminanceCoefficients:function(J,$=this.workingColorSpace){return J.fromArray(this.spaces[$].luminanceCoefficients)},define:function(J){Object.assign(this.spaces,J)},_getMatrix:function(J,$,Q){return J.copy(this.spaces[$].toXYZ).multiply(this.spaces[Q].fromXYZ)},_getDrawingBufferColorSpace:function(J){return this.spaces[J].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(J=this.workingColorSpace){return this.spaces[J].workingColorSpaceConfig.unpackColorSpace}};function i0(J){return J<0.04045?J*0.0773993808:Math.pow(J*0.9478672986+0.0521327014,2.4)}function g6(J){return J<0.0031308?J*12.92:1.055*Math.pow(J,0.41666)-0.055}var q9=[0.64,0.33,0.3,0.6,0.15,0.06],E9=[0.2126,0.7152,0.0722],V9=[0.3127,0.329],F9=new jJ().set(0.4123908,0.3575843,0.1804808,0.212639,0.7151687,0.0721923,0.0193308,0.1191948,0.9505322),D9=new jJ().set(3.2409699,-1.5373832,-0.4986108,-0.9692436,1.8759675,0.0415551,0.0556301,-0.203977,1.0569715);dJ.define({["srgb-linear"]:{primaries:q9,whitePoint:V9,transfer:"linear",toXYZ:F9,fromXYZ:D9,luminanceCoefficients:E9,workingColorSpaceConfig:{unpackColorSpace:"srgb"},outputColorSpaceConfig:{drawingBufferColorSpace:"srgb"}},["srgb"]:{primaries:q9,whitePoint:V9,transfer:"srgb",toXYZ:F9,fromXYZ:D9,luminanceCoefficients:E9,outputColorSpaceConfig:{drawingBufferColorSpace:"srgb"}}});var k6;class U${static getDataURL(J){if(/^data:/i.test(J.src))return J.src;if(typeof HTMLCanvasElement>"u")return J.src;let $;if(J instanceof HTMLCanvasElement)$=J;else{if(k6===void 0)k6=c7("canvas");k6.width=J.width,k6.height=J.height;let Q=k6.getContext("2d");if(J instanceof ImageData)Q.putImageData(J,0,0);else Q.drawImage(J,0,0,J.width,J.height);$=k6}if($.width>2048||$.height>2048)return console.warn("THREE.ImageUtils.getDataURL: Image converted to jpg for performance reasons",J),$.toDataURL("image/jpeg",0.6);else return $.toDataURL("image/png")}static sRGBToLinear(J){if(typeof HTMLImageElement<"u"&&J instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&J instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&J instanceof ImageBitmap){let $=c7("canvas");$.width=J.width,$.height=J.height;let Q=$.getContext("2d");Q.drawImage(J,0,0,J.width,J.height);let Z=Q.getImageData(0,0,J.width,J.height),W=Z.data;for(let Y=0;Y<W.length;Y++)W[Y]=i0(W[Y]/255)*255;return Q.putImageData(Z,0,0),$}else if(J.data){let $=J.data.slice(0);for(let Q=0;Q<$.length;Q++)if($ instanceof Uint8Array||$ instanceof Uint8ClampedArray)$[Q]=Math.floor(i0($[Q]/255)*255);else $[Q]=i0($[Q]);return{data:$,width:J.width,height:J.height}}else return console.warn("THREE.ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),J}}var $5=0;class b8{constructor(J=null){this.isSource=!0,Object.defineProperty(this,"id",{value:$5++}),this.uuid=H6(),this.data=J,this.dataReady=!0,this.version=0}set needsUpdate(J){if(J===!0)this.version++}toJSON(J){let $=J===void 0||typeof J==="string";if(!$&&J.images[this.uuid]!==void 0)return J.images[this.uuid];let Q={uuid:this.uuid,url:""},Z=this.data;if(Z!==null){let W;if(Array.isArray(Z)){W=[];for(let Y=0,X=Z.length;Y<X;Y++)if(Z[Y].isDataTexture)W.push(Y8(Z[Y].image));else W.push(Y8(Z[Y]))}else W=Y8(Z);Q.url=W}if(!$)J.images[this.uuid]=Q;return Q}}function Y8(J){if(typeof HTMLImageElement<"u"&&J instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&J instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&J instanceof ImageBitmap)return U$.getDataURL(J);else if(J.data)return{data:Array.from(J.data),width:J.width,height:J.height,type:J.data.constructor.name};else return console.warn("THREE.Texture: Unable to serialize Texture."),{}}var Q5=0;class M0 extends O6{constructor(J=M0.DEFAULT_IMAGE,$=M0.DEFAULT_MAPPING,Q=1001,Z=1001,W=1006,Y=1008,X=1023,H=1009,K=M0.DEFAULT_ANISOTROPY,G=""){super();this.isTexture=!0,Object.defineProperty(this,"id",{value:Q5++}),this.uuid=H6(),this.name="",this.source=new b8(J),this.mipmaps=[],this.mapping=$,this.channel=0,this.wrapS=Q,this.wrapT=Z,this.magFilter=W,this.minFilter=Y,this.anisotropy=K,this.format=X,this.internalFormat=null,this.type=H,this.offset=new uJ(0,0),this.repeat=new uJ(1,1),this.center=new uJ(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new jJ,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=G,this.userData={},this.version=0,this.onUpdate=null,this.isRenderTargetTexture=!1,this.pmremVersion=0}get image(){return this.source.data}set image(J=null){this.source.data=J}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}clone(){return new this.constructor().copy(this)}copy(J){return this.name=J.name,this.source=J.source,this.mipmaps=J.mipmaps.slice(0),this.mapping=J.mapping,this.channel=J.channel,this.wrapS=J.wrapS,this.wrapT=J.wrapT,this.magFilter=J.magFilter,this.minFilter=J.minFilter,this.anisotropy=J.anisotropy,this.format=J.format,this.internalFormat=J.internalFormat,this.type=J.type,this.offset.copy(J.offset),this.repeat.copy(J.repeat),this.center.copy(J.center),this.rotation=J.rotation,this.matrixAutoUpdate=J.matrixAutoUpdate,this.matrix.copy(J.matrix),this.generateMipmaps=J.generateMipmaps,this.premultiplyAlpha=J.premultiplyAlpha,this.flipY=J.flipY,this.unpackAlignment=J.unpackAlignment,this.colorSpace=J.colorSpace,this.userData=JSON.parse(JSON.stringify(J.userData)),this.needsUpdate=!0,this}toJSON(J){let $=J===void 0||typeof J==="string";if(!$&&J.textures[this.uuid]!==void 0)return J.textures[this.uuid];let Q={metadata:{version:4.6,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(J).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};if(Object.keys(this.userData).length>0)Q.userData=this.userData;if(!$)J.textures[this.uuid]=Q;return Q}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(J){if(this.mapping!==300)return J;if(J.applyMatrix3(this.matrix),J.x<0||J.x>1)switch(this.wrapS){case 1000:J.x=J.x-Math.floor(J.x);break;case 1001:J.x=J.x<0?0:1;break;case 1002:if(Math.abs(Math.floor(J.x)%2)===1)J.x=Math.ceil(J.x)-J.x;else J.x=J.x-Math.floor(J.x);break}if(J.y<0||J.y>1)switch(this.wrapT){case 1000:J.y=J.y-Math.floor(J.y);break;case 1001:J.y=J.y<0?0:1;break;case 1002:if(Math.abs(Math.floor(J.y)%2)===1)J.y=Math.ceil(J.y)-J.y;else J.y=J.y-Math.floor(J.y);break}if(this.flipY)J.y=1-J.y;return J}set needsUpdate(J){if(J===!0)this.version++,this.source.needsUpdate=!0}set needsPMREMUpdate(J){if(J===!0)this.pmremVersion++}}M0.DEFAULT_IMAGE=null;M0.DEFAULT_MAPPING=300;M0.DEFAULT_ANISOTROPY=1;class H0{constructor(J=0,$=0,Q=0,Z=1){H0.prototype.isVector4=!0,this.x=J,this.y=$,this.z=Q,this.w=Z}get width(){return this.z}set width(J){this.z=J}get height(){return this.w}set height(J){this.w=J}set(J,$,Q,Z){return this.x=J,this.y=$,this.z=Q,this.w=Z,this}setScalar(J){return this.x=J,this.y=J,this.z=J,this.w=J,this}setX(J){return this.x=J,this}setY(J){return this.y=J,this}setZ(J){return this.z=J,this}setW(J){return this.w=J,this}setComponent(J,$){switch(J){case 0:this.x=$;break;case 1:this.y=$;break;case 2:this.z=$;break;case 3:this.w=$;break;default:throw Error("index is out of range: "+J)}return this}getComponent(J){switch(J){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw Error("index is out of range: "+J)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(J){return this.x=J.x,this.y=J.y,this.z=J.z,this.w=J.w!==void 0?J.w:1,this}add(J){return this.x+=J.x,this.y+=J.y,this.z+=J.z,this.w+=J.w,this}addScalar(J){return this.x+=J,this.y+=J,this.z+=J,this.w+=J,this}addVectors(J,$){return this.x=J.x+$.x,this.y=J.y+$.y,this.z=J.z+$.z,this.w=J.w+$.w,this}addScaledVector(J,$){return this.x+=J.x*$,this.y+=J.y*$,this.z+=J.z*$,this.w+=J.w*$,this}sub(J){return this.x-=J.x,this.y-=J.y,this.z-=J.z,this.w-=J.w,this}subScalar(J){return this.x-=J,this.y-=J,this.z-=J,this.w-=J,this}subVectors(J,$){return this.x=J.x-$.x,this.y=J.y-$.y,this.z=J.z-$.z,this.w=J.w-$.w,this}multiply(J){return this.x*=J.x,this.y*=J.y,this.z*=J.z,this.w*=J.w,this}multiplyScalar(J){return this.x*=J,this.y*=J,this.z*=J,this.w*=J,this}applyMatrix4(J){let $=this.x,Q=this.y,Z=this.z,W=this.w,Y=J.elements;return this.x=Y[0]*$+Y[4]*Q+Y[8]*Z+Y[12]*W,this.y=Y[1]*$+Y[5]*Q+Y[9]*Z+Y[13]*W,this.z=Y[2]*$+Y[6]*Q+Y[10]*Z+Y[14]*W,this.w=Y[3]*$+Y[7]*Q+Y[11]*Z+Y[15]*W,this}divide(J){return this.x/=J.x,this.y/=J.y,this.z/=J.z,this.w/=J.w,this}divideScalar(J){return this.multiplyScalar(1/J)}setAxisAngleFromQuaternion(J){this.w=2*Math.acos(J.w);let $=Math.sqrt(1-J.w*J.w);if($<0.0001)this.x=1,this.y=0,this.z=0;else this.x=J.x/$,this.y=J.y/$,this.z=J.z/$;return this}setAxisAngleFromRotationMatrix(J){let $,Q,Z,W,Y=0.01,X=0.1,H=J.elements,K=H[0],G=H[4],E=H[8],U=H[1],q=H[5],D=H[9],N=H[2],O=H[6],V=H[10];if(Math.abs(G-U)<0.01&&Math.abs(E-N)<0.01&&Math.abs(D-O)<0.01){if(Math.abs(G+U)<0.1&&Math.abs(E+N)<0.1&&Math.abs(D+O)<0.1&&Math.abs(K+q+V-3)<0.1)return this.set(1,0,0,0),this;$=Math.PI;let A=(K+1)/2,z=(q+1)/2,_=(V+1)/2,b=(G+U)/4,L=(E+N)/4,P=(D+O)/4;if(A>z&&A>_)if(A<0.01)Q=0,Z=0.707106781,W=0.707106781;else Q=Math.sqrt(A),Z=b/Q,W=L/Q;else if(z>_)if(z<0.01)Q=0.707106781,Z=0,W=0.707106781;else Z=Math.sqrt(z),Q=b/Z,W=P/Z;else if(_<0.01)Q=0.707106781,Z=0.707106781,W=0;else W=Math.sqrt(_),Q=L/W,Z=P/W;return this.set(Q,Z,W,$),this}let F=Math.sqrt((O-D)*(O-D)+(E-N)*(E-N)+(U-G)*(U-G));if(Math.abs(F)<0.001)F=1;return this.x=(O-D)/F,this.y=(E-N)/F,this.z=(U-G)/F,this.w=Math.acos((K+q+V-1)/2),this}setFromMatrixPosition(J){let $=J.elements;return this.x=$[12],this.y=$[13],this.z=$[14],this.w=$[15],this}min(J){return this.x=Math.min(this.x,J.x),this.y=Math.min(this.y,J.y),this.z=Math.min(this.z,J.z),this.w=Math.min(this.w,J.w),this}max(J){return this.x=Math.max(this.x,J.x),this.y=Math.max(this.y,J.y),this.z=Math.max(this.z,J.z),this.w=Math.max(this.w,J.w),this}clamp(J,$){return this.x=Math.max(J.x,Math.min($.x,this.x)),this.y=Math.max(J.y,Math.min($.y,this.y)),this.z=Math.max(J.z,Math.min($.z,this.z)),this.w=Math.max(J.w,Math.min($.w,this.w)),this}clampScalar(J,$){return this.x=Math.max(J,Math.min($,this.x)),this.y=Math.max(J,Math.min($,this.y)),this.z=Math.max(J,Math.min($,this.z)),this.w=Math.max(J,Math.min($,this.w)),this}clampLength(J,$){let Q=this.length();return this.divideScalar(Q||1).multiplyScalar(Math.max(J,Math.min($,Q)))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(J){return this.x*J.x+this.y*J.y+this.z*J.z+this.w*J.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(J){return this.normalize().multiplyScalar(J)}lerp(J,$){return this.x+=(J.x-this.x)*$,this.y+=(J.y-this.y)*$,this.z+=(J.z-this.z)*$,this.w+=(J.w-this.w)*$,this}lerpVectors(J,$,Q){return this.x=J.x+($.x-J.x)*Q,this.y=J.y+($.y-J.y)*Q,this.z=J.z+($.z-J.z)*Q,this.w=J.w+($.w-J.w)*Q,this}equals(J){return J.x===this.x&&J.y===this.y&&J.z===this.z&&J.w===this.w}fromArray(J,$=0){return this.x=J[$],this.y=J[$+1],this.z=J[$+2],this.w=J[$+3],this}toArray(J=[],$=0){return J[$]=this.x,J[$+1]=this.y,J[$+2]=this.z,J[$+3]=this.w,J}fromBufferAttribute(J,$){return this.x=J.getX($),this.y=J.getY($),this.z=J.getZ($),this.w=J.getW($),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}}class q$ extends O6{constructor(J=1,$=1,Q={}){super();this.isRenderTarget=!0,this.width=J,this.height=$,this.depth=1,this.scissor=new H0(0,0,J,$),this.scissorTest=!1,this.viewport=new H0(0,0,J,$);let Z={width:J,height:$,depth:1};Q=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:1006,depthBuffer:!0,stencilBuffer:!1,resolveDepthBuffer:!0,resolveStencilBuffer:!0,depthTexture:null,samples:0,count:1},Q);let W=new M0(Z,Q.mapping,Q.wrapS,Q.wrapT,Q.magFilter,Q.minFilter,Q.format,Q.type,Q.anisotropy,Q.colorSpace);W.flipY=!1,W.generateMipmaps=Q.generateMipmaps,W.internalFormat=Q.internalFormat,this.textures=[];let Y=Q.count;for(let X=0;X<Y;X++)this.textures[X]=W.clone(),this.textures[X].isRenderTargetTexture=!0;this.depthBuffer=Q.depthBuffer,this.stencilBuffer=Q.stencilBuffer,this.resolveDepthBuffer=Q.resolveDepthBuffer,this.resolveStencilBuffer=Q.resolveStencilBuffer,this.depthTexture=Q.depthTexture,this.samples=Q.samples}get texture(){return this.textures[0]}set texture(J){this.textures[0]=J}setSize(J,$,Q=1){if(this.width!==J||this.height!==$||this.depth!==Q){this.width=J,this.height=$,this.depth=Q;for(let Z=0,W=this.textures.length;Z<W;Z++)this.textures[Z].image.width=J,this.textures[Z].image.height=$,this.textures[Z].image.depth=Q;this.dispose()}this.viewport.set(0,0,J,$),this.scissor.set(0,0,J,$)}clone(){return new this.constructor().copy(this)}copy(J){this.width=J.width,this.height=J.height,this.depth=J.depth,this.scissor.copy(J.scissor),this.scissorTest=J.scissorTest,this.viewport.copy(J.viewport),this.textures.length=0;for(let Q=0,Z=J.textures.length;Q<Z;Q++)this.textures[Q]=J.textures[Q].clone(),this.textures[Q].isRenderTargetTexture=!0;let $=Object.assign({},J.texture.image);if(this.texture.source=new b8($),this.depthBuffer=J.depthBuffer,this.stencilBuffer=J.stencilBuffer,this.resolveDepthBuffer=J.resolveDepthBuffer,this.resolveStencilBuffer=J.resolveStencilBuffer,J.depthTexture!==null)this.depthTexture=J.depthTexture.clone();return this.samples=J.samples,this}dispose(){this.dispatchEvent({type:"dispose"})}}class X6 extends q${constructor(J=1,$=1,Q={}){super(J,$,Q);this.isWebGLRenderTarget=!0}}class x8 extends M0{constructor(J=null,$=1,Q=1,Z=1){super(null);this.isDataArrayTexture=!0,this.image={data:J,width:$,height:Q,depth:Z},this.magFilter=1003,this.minFilter=1003,this.wrapR=1001,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}addLayerUpdate(J){this.layerUpdates.add(J)}clearLayerUpdates(){this.layerUpdates.clear()}}class E$ extends M0{constructor(J=null,$=1,Q=1,Z=1){super(null);this.isData3DTexture=!0,this.image={data:J,width:$,height:Q,depth:Z},this.magFilter=1003,this.minFilter=1003,this.wrapR=1001,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}class M6{constructor(J=0,$=0,Q=0,Z=1){this.isQuaternion=!0,this._x=J,this._y=$,this._z=Q,this._w=Z}static slerpFlat(J,$,Q,Z,W,Y,X){let H=Q[Z+0],K=Q[Z+1],G=Q[Z+2],E=Q[Z+3],U=W[Y+0],q=W[Y+1],D=W[Y+2],N=W[Y+3];if(X===0){J[$+0]=H,J[$+1]=K,J[$+2]=G,J[$+3]=E;return}if(X===1){J[$+0]=U,J[$+1]=q,J[$+2]=D,J[$+3]=N;return}if(E!==N||H!==U||K!==q||G!==D){let O=1-X,V=H*U+K*q+G*D+E*N,F=V>=0?1:-1,A=1-V*V;if(A>Number.EPSILON){let _=Math.sqrt(A),b=Math.atan2(_,V*F);O=Math.sin(O*b)/_,X=Math.sin(X*b)/_}let z=X*F;if(H=H*O+U*z,K=K*O+q*z,G=G*O+D*z,E=E*O+N*z,O===1-X){let _=1/Math.sqrt(H*H+K*K+G*G+E*E);H*=_,K*=_,G*=_,E*=_}}J[$]=H,J[$+1]=K,J[$+2]=G,J[$+3]=E}static multiplyQuaternionsFlat(J,$,Q,Z,W,Y){let X=Q[Z],H=Q[Z+1],K=Q[Z+2],G=Q[Z+3],E=W[Y],U=W[Y+1],q=W[Y+2],D=W[Y+3];return J[$]=X*D+G*E+H*q-K*U,J[$+1]=H*D+G*U+K*E-X*q,J[$+2]=K*D+G*q+X*U-H*E,J[$+3]=G*D-X*E-H*U-K*q,J}get x(){return this._x}set x(J){this._x=J,this._onChangeCallback()}get y(){return this._y}set y(J){this._y=J,this._onChangeCallback()}get z(){return this._z}set z(J){this._z=J,this._onChangeCallback()}get w(){return this._w}set w(J){this._w=J,this._onChangeCallback()}set(J,$,Q,Z){return this._x=J,this._y=$,this._z=Q,this._w=Z,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(J){return this._x=J.x,this._y=J.y,this._z=J.z,this._w=J.w,this._onChangeCallback(),this}setFromEuler(J,$=!0){let{_x:Q,_y:Z,_z:W,_order:Y}=J,X=Math.cos,H=Math.sin,K=X(Q/2),G=X(Z/2),E=X(W/2),U=H(Q/2),q=H(Z/2),D=H(W/2);switch(Y){case"XYZ":this._x=U*G*E+K*q*D,this._y=K*q*E-U*G*D,this._z=K*G*D+U*q*E,this._w=K*G*E-U*q*D;break;case"YXZ":this._x=U*G*E+K*q*D,this._y=K*q*E-U*G*D,this._z=K*G*D-U*q*E,this._w=K*G*E+U*q*D;break;case"ZXY":this._x=U*G*E-K*q*D,this._y=K*q*E+U*G*D,this._z=K*G*D+U*q*E,this._w=K*G*E-U*q*D;break;case"ZYX":this._x=U*G*E-K*q*D,this._y=K*q*E+U*G*D,this._z=K*G*D-U*q*E,this._w=K*G*E+U*q*D;break;case"YZX":this._x=U*G*E+K*q*D,this._y=K*q*E+U*G*D,this._z=K*G*D-U*q*E,this._w=K*G*E-U*q*D;break;case"XZY":this._x=U*G*E-K*q*D,this._y=K*q*E-U*G*D,this._z=K*G*D+U*q*E,this._w=K*G*E+U*q*D;break;default:console.warn("THREE.Quaternion: .setFromEuler() encountered an unknown order: "+Y)}if($===!0)this._onChangeCallback();return this}setFromAxisAngle(J,$){let Q=$/2,Z=Math.sin(Q);return this._x=J.x*Z,this._y=J.y*Z,this._z=J.z*Z,this._w=Math.cos(Q),this._onChangeCallback(),this}setFromRotationMatrix(J){let $=J.elements,Q=$[0],Z=$[4],W=$[8],Y=$[1],X=$[5],H=$[9],K=$[2],G=$[6],E=$[10],U=Q+X+E;if(U>0){let q=0.5/Math.sqrt(U+1);this._w=0.25/q,this._x=(G-H)*q,this._y=(W-K)*q,this._z=(Y-Z)*q}else if(Q>X&&Q>E){let q=2*Math.sqrt(1+Q-X-E);this._w=(G-H)/q,this._x=0.25*q,this._y=(Z+Y)/q,this._z=(W+K)/q}else if(X>E){let q=2*Math.sqrt(1+X-Q-E);this._w=(W-K)/q,this._x=(Z+Y)/q,this._y=0.25*q,this._z=(H+G)/q}else{let q=2*Math.sqrt(1+E-Q-X);this._w=(Y-Z)/q,this._x=(W+K)/q,this._y=(H+G)/q,this._z=0.25*q}return this._onChangeCallback(),this}setFromUnitVectors(J,$){let Q=J.dot($)+1;if(Q<Number.EPSILON)if(Q=0,Math.abs(J.x)>Math.abs(J.z))this._x=-J.y,this._y=J.x,this._z=0,this._w=Q;else this._x=0,this._y=-J.z,this._z=J.y,this._w=Q;else this._x=J.y*$.z-J.z*$.y,this._y=J.z*$.x-J.x*$.z,this._z=J.x*$.y-J.y*$.x,this._w=Q;return this.normalize()}angleTo(J){return 2*Math.acos(Math.abs(z0(this.dot(J),-1,1)))}rotateTowards(J,$){let Q=this.angleTo(J);if(Q===0)return this;let Z=Math.min(1,$/Q);return this.slerp(J,Z),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(J){return this._x*J._x+this._y*J._y+this._z*J._z+this._w*J._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let J=this.length();if(J===0)this._x=0,this._y=0,this._z=0,this._w=1;else J=1/J,this._x=this._x*J,this._y=this._y*J,this._z=this._z*J,this._w=this._w*J;return this._onChangeCallback(),this}multiply(J){return this.multiplyQuaternions(this,J)}premultiply(J){return this.multiplyQuaternions(J,this)}multiplyQuaternions(J,$){let{_x:Q,_y:Z,_z:W,_w:Y}=J,X=$._x,H=$._y,K=$._z,G=$._w;return this._x=Q*G+Y*X+Z*K-W*H,this._y=Z*G+Y*H+W*X-Q*K,this._z=W*G+Y*K+Q*H-Z*X,this._w=Y*G-Q*X-Z*H-W*K,this._onChangeCallback(),this}slerp(J,$){if($===0)return this;if($===1)return this.copy(J);let Q=this._x,Z=this._y,W=this._z,Y=this._w,X=Y*J._w+Q*J._x+Z*J._y+W*J._z;if(X<0)this._w=-J._w,this._x=-J._x,this._y=-J._y,this._z=-J._z,X=-X;else this.copy(J);if(X>=1)return this._w=Y,this._x=Q,this._y=Z,this._z=W,this;let H=1-X*X;if(H<=Number.EPSILON){let q=1-$;return this._w=q*Y+$*this._w,this._x=q*Q+$*this._x,this._y=q*Z+$*this._y,this._z=q*W+$*this._z,this.normalize(),this}let K=Math.sqrt(H),G=Math.atan2(K,X),E=Math.sin((1-$)*G)/K,U=Math.sin($*G)/K;return this._w=Y*E+this._w*U,this._x=Q*E+this._x*U,this._y=Z*E+this._y*U,this._z=W*E+this._z*U,this._onChangeCallback(),this}slerpQuaternions(J,$,Q){return this.copy(J).slerp($,Q)}random(){let J=2*Math.PI*Math.random(),$=2*Math.PI*Math.random(),Q=Math.random(),Z=Math.sqrt(1-Q),W=Math.sqrt(Q);return this.set(Z*Math.sin(J),Z*Math.cos(J),W*Math.sin($),W*Math.cos($))}equals(J){return J._x===this._x&&J._y===this._y&&J._z===this._z&&J._w===this._w}fromArray(J,$=0){return this._x=J[$],this._y=J[$+1],this._z=J[$+2],this._w=J[$+3],this._onChangeCallback(),this}toArray(J=[],$=0){return J[$]=this._x,J[$+1]=this._y,J[$+2]=this._z,J[$+3]=this._w,J}fromBufferAttribute(J,$){return this._x=J.getX($),this._y=J.getY($),this._z=J.getZ($),this._w=J.getW($),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(J){return this._onChangeCallback=J,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}}class v{constructor(J=0,$=0,Q=0){v.prototype.isVector3=!0,this.x=J,this.y=$,this.z=Q}set(J,$,Q){if(Q===void 0)Q=this.z;return this.x=J,this.y=$,this.z=Q,this}setScalar(J){return this.x=J,this.y=J,this.z=J,this}setX(J){return this.x=J,this}setY(J){return this.y=J,this}setZ(J){return this.z=J,this}setComponent(J,$){switch(J){case 0:this.x=$;break;case 1:this.y=$;break;case 2:this.z=$;break;default:throw Error("index is out of range: "+J)}return this}getComponent(J){switch(J){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw Error("index is out of range: "+J)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(J){return this.x=J.x,this.y=J.y,this.z=J.z,this}add(J){return this.x+=J.x,this.y+=J.y,this.z+=J.z,this}addScalar(J){return this.x+=J,this.y+=J,this.z+=J,this}addVectors(J,$){return this.x=J.x+$.x,this.y=J.y+$.y,this.z=J.z+$.z,this}addScaledVector(J,$){return this.x+=J.x*$,this.y+=J.y*$,this.z+=J.z*$,this}sub(J){return this.x-=J.x,this.y-=J.y,this.z-=J.z,this}subScalar(J){return this.x-=J,this.y-=J,this.z-=J,this}subVectors(J,$){return this.x=J.x-$.x,this.y=J.y-$.y,this.z=J.z-$.z,this}multiply(J){return this.x*=J.x,this.y*=J.y,this.z*=J.z,this}multiplyScalar(J){return this.x*=J,this.y*=J,this.z*=J,this}multiplyVectors(J,$){return this.x=J.x*$.x,this.y=J.y*$.y,this.z=J.z*$.z,this}applyEuler(J){return this.applyQuaternion(R9.setFromEuler(J))}applyAxisAngle(J,$){return this.applyQuaternion(R9.setFromAxisAngle(J,$))}applyMatrix3(J){let $=this.x,Q=this.y,Z=this.z,W=J.elements;return this.x=W[0]*$+W[3]*Q+W[6]*Z,this.y=W[1]*$+W[4]*Q+W[7]*Z,this.z=W[2]*$+W[5]*Q+W[8]*Z,this}applyNormalMatrix(J){return this.applyMatrix3(J).normalize()}applyMatrix4(J){let $=this.x,Q=this.y,Z=this.z,W=J.elements,Y=1/(W[3]*$+W[7]*Q+W[11]*Z+W[15]);return this.x=(W[0]*$+W[4]*Q+W[8]*Z+W[12])*Y,this.y=(W[1]*$+W[5]*Q+W[9]*Z+W[13])*Y,this.z=(W[2]*$+W[6]*Q+W[10]*Z+W[14])*Y,this}applyQuaternion(J){let $=this.x,Q=this.y,Z=this.z,W=J.x,Y=J.y,X=J.z,H=J.w,K=2*(Y*Z-X*Q),G=2*(X*$-W*Z),E=2*(W*Q-Y*$);return this.x=$+H*K+Y*E-X*G,this.y=Q+H*G+X*K-W*E,this.z=Z+H*E+W*G-Y*K,this}project(J){return this.applyMatrix4(J.matrixWorldInverse).applyMatrix4(J.projectionMatrix)}unproject(J){return this.applyMatrix4(J.projectionMatrixInverse).applyMatrix4(J.matrixWorld)}transformDirection(J){let $=this.x,Q=this.y,Z=this.z,W=J.elements;return this.x=W[0]*$+W[4]*Q+W[8]*Z,this.y=W[1]*$+W[5]*Q+W[9]*Z,this.z=W[2]*$+W[6]*Q+W[10]*Z,this.normalize()}divide(J){return this.x/=J.x,this.y/=J.y,this.z/=J.z,this}divideScalar(J){return this.multiplyScalar(1/J)}min(J){return this.x=Math.min(this.x,J.x),this.y=Math.min(this.y,J.y),this.z=Math.min(this.z,J.z),this}max(J){return this.x=Math.max(this.x,J.x),this.y=Math.max(this.y,J.y),this.z=Math.max(this.z,J.z),this}clamp(J,$){return this.x=Math.max(J.x,Math.min($.x,this.x)),this.y=Math.max(J.y,Math.min($.y,this.y)),this.z=Math.max(J.z,Math.min($.z,this.z)),this}clampScalar(J,$){return this.x=Math.max(J,Math.min($,this.x)),this.y=Math.max(J,Math.min($,this.y)),this.z=Math.max(J,Math.min($,this.z)),this}clampLength(J,$){let Q=this.length();return this.divideScalar(Q||1).multiplyScalar(Math.max(J,Math.min($,Q)))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(J){return this.x*J.x+this.y*J.y+this.z*J.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(J){return this.normalize().multiplyScalar(J)}lerp(J,$){return this.x+=(J.x-this.x)*$,this.y+=(J.y-this.y)*$,this.z+=(J.z-this.z)*$,this}lerpVectors(J,$,Q){return this.x=J.x+($.x-J.x)*Q,this.y=J.y+($.y-J.y)*Q,this.z=J.z+($.z-J.z)*Q,this}cross(J){return this.crossVectors(this,J)}crossVectors(J,$){let{x:Q,y:Z,z:W}=J,Y=$.x,X=$.y,H=$.z;return this.x=Z*H-W*X,this.y=W*Y-Q*H,this.z=Q*X-Z*Y,this}projectOnVector(J){let $=J.lengthSq();if($===0)return this.set(0,0,0);let Q=J.dot(this)/$;return this.copy(J).multiplyScalar(Q)}projectOnPlane(J){return H8.copy(this).projectOnVector(J),this.sub(H8)}reflect(J){return this.sub(H8.copy(J).multiplyScalar(2*this.dot(J)))}angleTo(J){let $=Math.sqrt(this.lengthSq()*J.lengthSq());if($===0)return Math.PI/2;let Q=this.dot(J)/$;return Math.acos(z0(Q,-1,1))}distanceTo(J){return Math.sqrt(this.distanceToSquared(J))}distanceToSquared(J){let $=this.x-J.x,Q=this.y-J.y,Z=this.z-J.z;return $*$+Q*Q+Z*Z}manhattanDistanceTo(J){return Math.abs(this.x-J.x)+Math.abs(this.y-J.y)+Math.abs(this.z-J.z)}setFromSpherical(J){return this.setFromSphericalCoords(J.radius,J.phi,J.theta)}setFromSphericalCoords(J,$,Q){let Z=Math.sin($)*J;return this.x=Z*Math.sin(Q),this.y=Math.cos($)*J,this.z=Z*Math.cos(Q),this}setFromCylindrical(J){return this.setFromCylindricalCoords(J.radius,J.theta,J.y)}setFromCylindricalCoords(J,$,Q){return this.x=J*Math.sin($),this.y=Q,this.z=J*Math.cos($),this}setFromMatrixPosition(J){let $=J.elements;return this.x=$[12],this.y=$[13],this.z=$[14],this}setFromMatrixScale(J){let $=this.setFromMatrixColumn(J,0).length(),Q=this.setFromMatrixColumn(J,1).length(),Z=this.setFromMatrixColumn(J,2).length();return this.x=$,this.y=Q,this.z=Z,this}setFromMatrixColumn(J,$){return this.fromArray(J.elements,$*4)}setFromMatrix3Column(J,$){return this.fromArray(J.elements,$*3)}setFromEuler(J){return this.x=J._x,this.y=J._y,this.z=J._z,this}setFromColor(J){return this.x=J.r,this.y=J.g,this.z=J.b,this}equals(J){return J.x===this.x&&J.y===this.y&&J.z===this.z}fromArray(J,$=0){return this.x=J[$],this.y=J[$+1],this.z=J[$+2],this}toArray(J=[],$=0){return J[$]=this.x,J[$+1]=this.y,J[$+2]=this.z,J}fromBufferAttribute(J,$){return this.x=J.getX($),this.y=J.getY($),this.z=J.getZ($),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){let J=Math.random()*Math.PI*2,$=Math.random()*2-1,Q=Math.sqrt(1-$*$);return this.x=Q*Math.cos(J),this.y=$,this.z=Q*Math.sin(J),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}}var H8=new v,R9=new M6;class u6{constructor(J=new v(1/0,1/0,1/0),$=new v(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=J,this.max=$}set(J,$){return this.min.copy(J),this.max.copy($),this}setFromArray(J){this.makeEmpty();for(let $=0,Q=J.length;$<Q;$+=3)this.expandByPoint(y0.fromArray(J,$));return this}setFromBufferAttribute(J){this.makeEmpty();for(let $=0,Q=J.count;$<Q;$++)this.expandByPoint(y0.fromBufferAttribute(J,$));return this}setFromPoints(J){this.makeEmpty();for(let $=0,Q=J.length;$<Q;$++)this.expandByPoint(J[$]);return this}setFromCenterAndSize(J,$){let Q=y0.copy($).multiplyScalar(0.5);return this.min.copy(J).sub(Q),this.max.copy(J).add(Q),this}setFromObject(J,$=!1){return this.makeEmpty(),this.expandByObject(J,$)}clone(){return new this.constructor().copy(this)}copy(J){return this.min.copy(J.min),this.max.copy(J.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(J){return this.isEmpty()?J.set(0,0,0):J.addVectors(this.min,this.max).multiplyScalar(0.5)}getSize(J){return this.isEmpty()?J.set(0,0,0):J.subVectors(this.max,this.min)}expandByPoint(J){return this.min.min(J),this.max.max(J),this}expandByVector(J){return this.min.sub(J),this.max.add(J),this}expandByScalar(J){return this.min.addScalar(-J),this.max.addScalar(J),this}expandByObject(J,$=!1){J.updateWorldMatrix(!1,!1);let Q=J.geometry;if(Q!==void 0){let W=Q.getAttribute("position");if($===!0&&W!==void 0&&J.isInstancedMesh!==!0)for(let Y=0,X=W.count;Y<X;Y++){if(J.isMesh===!0)J.getVertexPosition(Y,y0);else y0.fromBufferAttribute(W,Y);y0.applyMatrix4(J.matrixWorld),this.expandByPoint(y0)}else{if(J.boundingBox!==void 0){if(J.boundingBox===null)J.computeBoundingBox();E7.copy(J.boundingBox)}else{if(Q.boundingBox===null)Q.computeBoundingBox();E7.copy(Q.boundingBox)}E7.applyMatrix4(J.matrixWorld),this.union(E7)}}let Z=J.children;for(let W=0,Y=Z.length;W<Y;W++)this.expandByObject(Z[W],$);return this}containsPoint(J){return J.x>=this.min.x&&J.x<=this.max.x&&J.y>=this.min.y&&J.y<=this.max.y&&J.z>=this.min.z&&J.z<=this.max.z}containsBox(J){return this.min.x<=J.min.x&&J.max.x<=this.max.x&&this.min.y<=J.min.y&&J.max.y<=this.max.y&&this.min.z<=J.min.z&&J.max.z<=this.max.z}getParameter(J,$){return $.set((J.x-this.min.x)/(this.max.x-this.min.x),(J.y-this.min.y)/(this.max.y-this.min.y),(J.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(J){return J.max.x>=this.min.x&&J.min.x<=this.max.x&&J.max.y>=this.min.y&&J.min.y<=this.max.y&&J.max.z>=this.min.z&&J.min.z<=this.max.z}intersectsSphere(J){return this.clampPoint(J.center,y0),y0.distanceToSquared(J.center)<=J.radius*J.radius}intersectsPlane(J){let $,Q;if(J.normal.x>0)$=J.normal.x*this.min.x,Q=J.normal.x*this.max.x;else $=J.normal.x*this.max.x,Q=J.normal.x*this.min.x;if(J.normal.y>0)$+=J.normal.y*this.min.y,Q+=J.normal.y*this.max.y;else $+=J.normal.y*this.max.y,Q+=J.normal.y*this.min.y;if(J.normal.z>0)$+=J.normal.z*this.min.z,Q+=J.normal.z*this.max.z;else $+=J.normal.z*this.max.z,Q+=J.normal.z*this.min.z;return $<=-J.constant&&Q>=-J.constant}intersectsTriangle(J){if(this.isEmpty())return!1;this.getCenter(o6),V7.subVectors(this.max,o6),A6.subVectors(J.a,o6),w6.subVectors(J.b,o6),L6.subVectors(J.c,o6),e0.subVectors(w6,A6),J6.subVectors(L6,w6),U6.subVectors(A6,L6);let $=[0,-e0.z,e0.y,0,-J6.z,J6.y,0,-U6.z,U6.y,e0.z,0,-e0.x,J6.z,0,-J6.x,U6.z,0,-U6.x,-e0.y,e0.x,0,-J6.y,J6.x,0,-U6.y,U6.x,0];if(!X8($,A6,w6,L6,V7))return!1;if($=[1,0,0,0,1,0,0,0,1],!X8($,A6,w6,L6,V7))return!1;return F7.crossVectors(e0,J6),$=[F7.x,F7.y,F7.z],X8($,A6,w6,L6,V7)}clampPoint(J,$){return $.copy(J).clamp(this.min,this.max)}distanceToPoint(J){return this.clampPoint(J,y0).distanceTo(J)}getBoundingSphere(J){if(this.isEmpty())J.makeEmpty();else this.getCenter(J.center),J.radius=this.getSize(y0).length()*0.5;return J}intersect(J){if(this.min.max(J.min),this.max.min(J.max),this.isEmpty())this.makeEmpty();return this}union(J){return this.min.min(J.min),this.max.max(J.max),this}applyMatrix4(J){if(this.isEmpty())return this;return u0[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(J),u0[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(J),u0[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(J),u0[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(J),u0[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(J),u0[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(J),u0[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(J),u0[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(J),this.setFromPoints(u0),this}translate(J){return this.min.add(J),this.max.add(J),this}equals(J){return J.min.equals(this.min)&&J.max.equals(this.max)}}var u0=[new v,new v,new v,new v,new v,new v,new v,new v],y0=new v,E7=new u6,A6=new v,w6=new v,L6=new v,e0=new v,J6=new v,U6=new v,o6=new v,V7=new v,F7=new v,q6=new v;function X8(J,$,Q,Z,W){for(let Y=0,X=J.length-3;Y<=X;Y+=3){q6.fromArray(J,Y);let H=W.x*Math.abs(q6.x)+W.y*Math.abs(q6.y)+W.z*Math.abs(q6.z),K=$.dot(q6),G=Q.dot(q6),E=Z.dot(q6);if(Math.max(-Math.max(K,G,E),Math.min(K,G,E))>H)return!1}return!0}var Z5=new u6,a6=new v,K8=new v;class l6{constructor(J=new v,$=-1){this.isSphere=!0,this.center=J,this.radius=$}set(J,$){return this.center.copy(J),this.radius=$,this}setFromPoints(J,$){let Q=this.center;if($!==void 0)Q.copy($);else Z5.setFromPoints(J).getCenter(Q);let Z=0;for(let W=0,Y=J.length;W<Y;W++)Z=Math.max(Z,Q.distanceToSquared(J[W]));return this.radius=Math.sqrt(Z),this}copy(J){return this.center.copy(J.center),this.radius=J.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(J){return J.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(J){return J.distanceTo(this.center)-this.radius}intersectsSphere(J){let $=this.radius+J.radius;return J.center.distanceToSquared(this.center)<=$*$}intersectsBox(J){return J.intersectsSphere(this)}intersectsPlane(J){return Math.abs(J.distanceToPoint(this.center))<=this.radius}clampPoint(J,$){let Q=this.center.distanceToSquared(J);if($.copy(J),Q>this.radius*this.radius)$.sub(this.center).normalize(),$.multiplyScalar(this.radius).add(this.center);return $}getBoundingBox(J){if(this.isEmpty())return J.makeEmpty(),J;return J.set(this.center,this.center),J.expandByScalar(this.radius),J}applyMatrix4(J){return this.center.applyMatrix4(J),this.radius=this.radius*J.getMaxScaleOnAxis(),this}translate(J){return this.center.add(J),this}expandByPoint(J){if(this.isEmpty())return this.center.copy(J),this.radius=0,this;a6.subVectors(J,this.center);let $=a6.lengthSq();if($>this.radius*this.radius){let Q=Math.sqrt($),Z=(Q-this.radius)*0.5;this.center.addScaledVector(a6,Z/Q),this.radius+=Z}return this}union(J){if(J.isEmpty())return this;if(this.isEmpty())return this.copy(J),this;if(this.center.equals(J.center)===!0)this.radius=Math.max(this.radius,J.radius);else K8.subVectors(J.center,this.center).setLength(J.radius),this.expandByPoint(a6.copy(J.center).add(K8)),this.expandByPoint(a6.copy(J.center).sub(K8));return this}equals(J){return J.center.equals(this.center)&&J.radius===this.radius}clone(){return new this.constructor().copy(this)}}var l0=new v,G8=new v,D7=new v,$6=new v,U8=new v,R7=new v,q8=new v;class o7{constructor(J=new v,$=new v(0,0,-1)){this.origin=J,this.direction=$}set(J,$){return this.origin.copy(J),this.direction.copy($),this}copy(J){return this.origin.copy(J.origin),this.direction.copy(J.direction),this}at(J,$){return $.copy(this.origin).addScaledVector(this.direction,J)}lookAt(J){return this.direction.copy(J).sub(this.origin).normalize(),this}recast(J){return this.origin.copy(this.at(J,l0)),this}closestPointToPoint(J,$){$.subVectors(J,this.origin);let Q=$.dot(this.direction);if(Q<0)return $.copy(this.origin);return $.copy(this.origin).addScaledVector(this.direction,Q)}distanceToPoint(J){return Math.sqrt(this.distanceSqToPoint(J))}distanceSqToPoint(J){let $=l0.subVectors(J,this.origin).dot(this.direction);if($<0)return this.origin.distanceToSquared(J);return l0.copy(this.origin).addScaledVector(this.direction,$),l0.distanceToSquared(J)}distanceSqToSegment(J,$,Q,Z){G8.copy(J).add($).multiplyScalar(0.5),D7.copy($).sub(J).normalize(),$6.copy(this.origin).sub(G8);let W=J.distanceTo($)*0.5,Y=-this.direction.dot(D7),X=$6.dot(this.direction),H=-$6.dot(D7),K=$6.lengthSq(),G=Math.abs(1-Y*Y),E,U,q,D;if(G>0)if(E=Y*H-X,U=Y*X-H,D=W*G,E>=0)if(U>=-D)if(U<=D){let N=1/G;E*=N,U*=N,q=E*(E+Y*U+2*X)+U*(Y*E+U+2*H)+K}else U=W,E=Math.max(0,-(Y*U+X)),q=-E*E+U*(U+2*H)+K;else U=-W,E=Math.max(0,-(Y*U+X)),q=-E*E+U*(U+2*H)+K;else if(U<=-D)E=Math.max(0,-(-Y*W+X)),U=E>0?-W:Math.min(Math.max(-W,-H),W),q=-E*E+U*(U+2*H)+K;else if(U<=D)E=0,U=Math.min(Math.max(-W,-H),W),q=U*(U+2*H)+K;else E=Math.max(0,-(Y*W+X)),U=E>0?W:Math.min(Math.max(-W,-H),W),q=-E*E+U*(U+2*H)+K;else U=Y>0?-W:W,E=Math.max(0,-(Y*U+X)),q=-E*E+U*(U+2*H)+K;if(Q)Q.copy(this.origin).addScaledVector(this.direction,E);if(Z)Z.copy(G8).addScaledVector(D7,U);return q}intersectSphere(J,$){l0.subVectors(J.center,this.origin);let Q=l0.dot(this.direction),Z=l0.dot(l0)-Q*Q,W=J.radius*J.radius;if(Z>W)return null;let Y=Math.sqrt(W-Z),X=Q-Y,H=Q+Y;if(H<0)return null;if(X<0)return this.at(H,$);return this.at(X,$)}intersectsSphere(J){return this.distanceSqToPoint(J.center)<=J.radius*J.radius}distanceToPlane(J){let $=J.normal.dot(this.direction);if($===0){if(J.distanceToPoint(this.origin)===0)return 0;return null}let Q=-(this.origin.dot(J.normal)+J.constant)/$;return Q>=0?Q:null}intersectPlane(J,$){let Q=this.distanceToPlane(J);if(Q===null)return null;return this.at(Q,$)}intersectsPlane(J){let $=J.distanceToPoint(this.origin);if($===0)return!0;if(J.normal.dot(this.direction)*$<0)return!0;return!1}intersectBox(J,$){let Q,Z,W,Y,X,H,K=1/this.direction.x,G=1/this.direction.y,E=1/this.direction.z,U=this.origin;if(K>=0)Q=(J.min.x-U.x)*K,Z=(J.max.x-U.x)*K;else Q=(J.max.x-U.x)*K,Z=(J.min.x-U.x)*K;if(G>=0)W=(J.min.y-U.y)*G,Y=(J.max.y-U.y)*G;else W=(J.max.y-U.y)*G,Y=(J.min.y-U.y)*G;if(Q>Y||W>Z)return null;if(W>Q||isNaN(Q))Q=W;if(Y<Z||isNaN(Z))Z=Y;if(E>=0)X=(J.min.z-U.z)*E,H=(J.max.z-U.z)*E;else X=(J.max.z-U.z)*E,H=(J.min.z-U.z)*E;if(Q>H||X>Z)return null;if(X>Q||Q!==Q)Q=X;if(H<Z||Z!==Z)Z=H;if(Z<0)return null;return this.at(Q>=0?Q:Z,$)}intersectsBox(J){return this.intersectBox(J,l0)!==null}intersectTriangle(J,$,Q,Z,W){U8.subVectors($,J),R7.subVectors(Q,J),q8.crossVectors(U8,R7);let Y=this.direction.dot(q8),X;if(Y>0){if(Z)return null;X=1}else if(Y<0)X=-1,Y=-Y;else return null;$6.subVectors(this.origin,J);let H=X*this.direction.dot(R7.crossVectors($6,R7));if(H<0)return null;let K=X*this.direction.dot(U8.cross($6));if(K<0)return null;if(H+K>Y)return null;let G=-X*$6.dot(q8);if(G<0)return null;return this.at(G/Y,W)}applyMatrix4(J){return this.origin.applyMatrix4(J),this.direction.transformDirection(J),this}equals(J){return J.origin.equals(this.origin)&&J.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}}class Z0{constructor(J,$,Q,Z,W,Y,X,H,K,G,E,U,q,D,N,O){if(Z0.prototype.isMatrix4=!0,this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],J!==void 0)this.set(J,$,Q,Z,W,Y,X,H,K,G,E,U,q,D,N,O)}set(J,$,Q,Z,W,Y,X,H,K,G,E,U,q,D,N,O){let V=this.elements;return V[0]=J,V[4]=$,V[8]=Q,V[12]=Z,V[1]=W,V[5]=Y,V[9]=X,V[13]=H,V[2]=K,V[6]=G,V[10]=E,V[14]=U,V[3]=q,V[7]=D,V[11]=N,V[15]=O,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new Z0().fromArray(this.elements)}copy(J){let $=this.elements,Q=J.elements;return $[0]=Q[0],$[1]=Q[1],$[2]=Q[2],$[3]=Q[3],$[4]=Q[4],$[5]=Q[5],$[6]=Q[6],$[7]=Q[7],$[8]=Q[8],$[9]=Q[9],$[10]=Q[10],$[11]=Q[11],$[12]=Q[12],$[13]=Q[13],$[14]=Q[14],$[15]=Q[15],this}copyPosition(J){let $=this.elements,Q=J.elements;return $[12]=Q[12],$[13]=Q[13],$[14]=Q[14],this}setFromMatrix3(J){let $=J.elements;return this.set($[0],$[3],$[6],0,$[1],$[4],$[7],0,$[2],$[5],$[8],0,0,0,0,1),this}extractBasis(J,$,Q){return J.setFromMatrixColumn(this,0),$.setFromMatrixColumn(this,1),Q.setFromMatrixColumn(this,2),this}makeBasis(J,$,Q){return this.set(J.x,$.x,Q.x,0,J.y,$.y,Q.y,0,J.z,$.z,Q.z,0,0,0,0,1),this}extractRotation(J){let $=this.elements,Q=J.elements,Z=1/_6.setFromMatrixColumn(J,0).length(),W=1/_6.setFromMatrixColumn(J,1).length(),Y=1/_6.setFromMatrixColumn(J,2).length();return $[0]=Q[0]*Z,$[1]=Q[1]*Z,$[2]=Q[2]*Z,$[3]=0,$[4]=Q[4]*W,$[5]=Q[5]*W,$[6]=Q[6]*W,$[7]=0,$[8]=Q[8]*Y,$[9]=Q[9]*Y,$[10]=Q[10]*Y,$[11]=0,$[12]=0,$[13]=0,$[14]=0,$[15]=1,this}makeRotationFromEuler(J){let $=this.elements,Q=J.x,Z=J.y,W=J.z,Y=Math.cos(Q),X=Math.sin(Q),H=Math.cos(Z),K=Math.sin(Z),G=Math.cos(W),E=Math.sin(W);if(J.order==="XYZ"){let U=Y*G,q=Y*E,D=X*G,N=X*E;$[0]=H*G,$[4]=-H*E,$[8]=K,$[1]=q+D*K,$[5]=U-N*K,$[9]=-X*H,$[2]=N-U*K,$[6]=D+q*K,$[10]=Y*H}else if(J.order==="YXZ"){let U=H*G,q=H*E,D=K*G,N=K*E;$[0]=U+N*X,$[4]=D*X-q,$[8]=Y*K,$[1]=Y*E,$[5]=Y*G,$[9]=-X,$[2]=q*X-D,$[6]=N+U*X,$[10]=Y*H}else if(J.order==="ZXY"){let U=H*G,q=H*E,D=K*G,N=K*E;$[0]=U-N*X,$[4]=-Y*E,$[8]=D+q*X,$[1]=q+D*X,$[5]=Y*G,$[9]=N-U*X,$[2]=-Y*K,$[6]=X,$[10]=Y*H}else if(J.order==="ZYX"){let U=Y*G,q=Y*E,D=X*G,N=X*E;$[0]=H*G,$[4]=D*K-q,$[8]=U*K+N,$[1]=H*E,$[5]=N*K+U,$[9]=q*K-D,$[2]=-K,$[6]=X*H,$[10]=Y*H}else if(J.order==="YZX"){let U=Y*H,q=Y*K,D=X*H,N=X*K;$[0]=H*G,$[4]=N-U*E,$[8]=D*E+q,$[1]=E,$[5]=Y*G,$[9]=-X*G,$[2]=-K*G,$[6]=q*E+D,$[10]=U-N*E}else if(J.order==="XZY"){let U=Y*H,q=Y*K,D=X*H,N=X*K;$[0]=H*G,$[4]=-E,$[8]=K*G,$[1]=U*E+N,$[5]=Y*G,$[9]=q*E-D,$[2]=D*E-q,$[6]=X*G,$[10]=N*E+U}return $[3]=0,$[7]=0,$[11]=0,$[12]=0,$[13]=0,$[14]=0,$[15]=1,this}makeRotationFromQuaternion(J){return this.compose(W5,J,Y5)}lookAt(J,$,Q){let Z=this.elements;if(w0.subVectors(J,$),w0.lengthSq()===0)w0.z=1;if(w0.normalize(),Q6.crossVectors(Q,w0),Q6.lengthSq()===0){if(Math.abs(Q.z)===1)w0.x+=0.0001;else w0.z+=0.0001;w0.normalize(),Q6.crossVectors(Q,w0)}return Q6.normalize(),N7.crossVectors(w0,Q6),Z[0]=Q6.x,Z[4]=N7.x,Z[8]=w0.x,Z[1]=Q6.y,Z[5]=N7.y,Z[9]=w0.y,Z[2]=Q6.z,Z[6]=N7.z,Z[10]=w0.z,this}multiply(J){return this.multiplyMatrices(this,J)}premultiply(J){return this.multiplyMatrices(J,this)}multiplyMatrices(J,$){let Q=J.elements,Z=$.elements,W=this.elements,Y=Q[0],X=Q[4],H=Q[8],K=Q[12],G=Q[1],E=Q[5],U=Q[9],q=Q[13],D=Q[2],N=Q[6],O=Q[10],V=Q[14],F=Q[3],A=Q[7],z=Q[11],_=Q[15],b=Z[0],L=Z[4],P=Z[8],p=Z[12],B=Z[1],k=Z[5],T=Z[9],x=Z[13],m=Z[2],u=Z[6],a=Z[10],l=Z[14],t=Z[3],g=Z[7],XJ=Z[11],ZJ=Z[15];return W[0]=Y*b+X*B+H*m+K*t,W[4]=Y*L+X*k+H*u+K*g,W[8]=Y*P+X*T+H*a+K*XJ,W[12]=Y*p+X*x+H*l+K*ZJ,W[1]=G*b+E*B+U*m+q*t,W[5]=G*L+E*k+U*u+q*g,W[9]=G*P+E*T+U*a+q*XJ,W[13]=G*p+E*x+U*l+q*ZJ,W[2]=D*b+N*B+O*m+V*t,W[6]=D*L+N*k+O*u+V*g,W[10]=D*P+N*T+O*a+V*XJ,W[14]=D*p+N*x+O*l+V*ZJ,W[3]=F*b+A*B+z*m+_*t,W[7]=F*L+A*k+z*u+_*g,W[11]=F*P+A*T+z*a+_*XJ,W[15]=F*p+A*x+z*l+_*ZJ,this}multiplyScalar(J){let $=this.elements;return $[0]*=J,$[4]*=J,$[8]*=J,$[12]*=J,$[1]*=J,$[5]*=J,$[9]*=J,$[13]*=J,$[2]*=J,$[6]*=J,$[10]*=J,$[14]*=J,$[3]*=J,$[7]*=J,$[11]*=J,$[15]*=J,this}determinant(){let J=this.elements,$=J[0],Q=J[4],Z=J[8],W=J[12],Y=J[1],X=J[5],H=J[9],K=J[13],G=J[2],E=J[6],U=J[10],q=J[14],D=J[3],N=J[7],O=J[11],V=J[15];return D*(+W*H*E-Z*K*E-W*X*U+Q*K*U+Z*X*q-Q*H*q)+N*(+$*H*q-$*K*U+W*Y*U-Z*Y*q+Z*K*G-W*H*G)+O*(+$*K*E-$*X*q-W*Y*E+Q*Y*q+W*X*G-Q*K*G)+V*(-Z*X*G-$*H*E+$*X*U+Z*Y*E-Q*Y*U+Q*H*G)}transpose(){let J=this.elements,$;return $=J[1],J[1]=J[4],J[4]=$,$=J[2],J[2]=J[8],J[8]=$,$=J[6],J[6]=J[9],J[9]=$,$=J[3],J[3]=J[12],J[12]=$,$=J[7],J[7]=J[13],J[13]=$,$=J[11],J[11]=J[14],J[14]=$,this}setPosition(J,$,Q){let Z=this.elements;if(J.isVector3)Z[12]=J.x,Z[13]=J.y,Z[14]=J.z;else Z[12]=J,Z[13]=$,Z[14]=Q;return this}invert(){let J=this.elements,$=J[0],Q=J[1],Z=J[2],W=J[3],Y=J[4],X=J[5],H=J[6],K=J[7],G=J[8],E=J[9],U=J[10],q=J[11],D=J[12],N=J[13],O=J[14],V=J[15],F=E*O*K-N*U*K+N*H*q-X*O*q-E*H*V+X*U*V,A=D*U*K-G*O*K-D*H*q+Y*O*q+G*H*V-Y*U*V,z=G*N*K-D*E*K+D*X*q-Y*N*q-G*X*V+Y*E*V,_=D*E*H-G*N*H-D*X*U+Y*N*U+G*X*O-Y*E*O,b=$*F+Q*A+Z*z+W*_;if(b===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);let L=1/b;return J[0]=F*L,J[1]=(N*U*W-E*O*W-N*Z*q+Q*O*q+E*Z*V-Q*U*V)*L,J[2]=(X*O*W-N*H*W+N*Z*K-Q*O*K-X*Z*V+Q*H*V)*L,J[3]=(E*H*W-X*U*W-E*Z*K+Q*U*K+X*Z*q-Q*H*q)*L,J[4]=A*L,J[5]=(G*O*W-D*U*W+D*Z*q-$*O*q-G*Z*V+$*U*V)*L,J[6]=(D*H*W-Y*O*W-D*Z*K+$*O*K+Y*Z*V-$*H*V)*L,J[7]=(Y*U*W-G*H*W+G*Z*K-$*U*K-Y*Z*q+$*H*q)*L,J[8]=z*L,J[9]=(D*E*W-G*N*W-D*Q*q+$*N*q+G*Q*V-$*E*V)*L,J[10]=(Y*N*W-D*X*W+D*Q*K-$*N*K-Y*Q*V+$*X*V)*L,J[11]=(G*X*W-Y*E*W-G*Q*K+$*E*K+Y*Q*q-$*X*q)*L,J[12]=_*L,J[13]=(G*N*Z-D*E*Z+D*Q*U-$*N*U-G*Q*O+$*E*O)*L,J[14]=(D*X*Z-Y*N*Z-D*Q*H+$*N*H+Y*Q*O-$*X*O)*L,J[15]=(Y*E*Z-G*X*Z+G*Q*H-$*E*H-Y*Q*U+$*X*U)*L,this}scale(J){let $=this.elements,Q=J.x,Z=J.y,W=J.z;return $[0]*=Q,$[4]*=Z,$[8]*=W,$[1]*=Q,$[5]*=Z,$[9]*=W,$[2]*=Q,$[6]*=Z,$[10]*=W,$[3]*=Q,$[7]*=Z,$[11]*=W,this}getMaxScaleOnAxis(){let J=this.elements,$=J[0]*J[0]+J[1]*J[1]+J[2]*J[2],Q=J[4]*J[4]+J[5]*J[5]+J[6]*J[6],Z=J[8]*J[8]+J[9]*J[9]+J[10]*J[10];return Math.sqrt(Math.max($,Q,Z))}makeTranslation(J,$,Q){if(J.isVector3)this.set(1,0,0,J.x,0,1,0,J.y,0,0,1,J.z,0,0,0,1);else this.set(1,0,0,J,0,1,0,$,0,0,1,Q,0,0,0,1);return this}makeRotationX(J){let $=Math.cos(J),Q=Math.sin(J);return this.set(1,0,0,0,0,$,-Q,0,0,Q,$,0,0,0,0,1),this}makeRotationY(J){let $=Math.cos(J),Q=Math.sin(J);return this.set($,0,Q,0,0,1,0,0,-Q,0,$,0,0,0,0,1),this}makeRotationZ(J){let $=Math.cos(J),Q=Math.sin(J);return this.set($,-Q,0,0,Q,$,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(J,$){let Q=Math.cos($),Z=Math.sin($),W=1-Q,Y=J.x,X=J.y,H=J.z,K=W*Y,G=W*X;return this.set(K*Y+Q,K*X-Z*H,K*H+Z*X,0,K*X+Z*H,G*X+Q,G*H-Z*Y,0,K*H-Z*X,G*H+Z*Y,W*H*H+Q,0,0,0,0,1),this}makeScale(J,$,Q){return this.set(J,0,0,0,0,$,0,0,0,0,Q,0,0,0,0,1),this}makeShear(J,$,Q,Z,W,Y){return this.set(1,Q,W,0,J,1,Y,0,$,Z,1,0,0,0,0,1),this}compose(J,$,Q){let Z=this.elements,W=$._x,Y=$._y,X=$._z,H=$._w,K=W+W,G=Y+Y,E=X+X,U=W*K,q=W*G,D=W*E,N=Y*G,O=Y*E,V=X*E,F=H*K,A=H*G,z=H*E,_=Q.x,b=Q.y,L=Q.z;return Z[0]=(1-(N+V))*_,Z[1]=(q+z)*_,Z[2]=(D-A)*_,Z[3]=0,Z[4]=(q-z)*b,Z[5]=(1-(U+V))*b,Z[6]=(O+F)*b,Z[7]=0,Z[8]=(D+A)*L,Z[9]=(O-F)*L,Z[10]=(1-(U+N))*L,Z[11]=0,Z[12]=J.x,Z[13]=J.y,Z[14]=J.z,Z[15]=1,this}decompose(J,$,Q){let Z=this.elements,W=_6.set(Z[0],Z[1],Z[2]).length(),Y=_6.set(Z[4],Z[5],Z[6]).length(),X=_6.set(Z[8],Z[9],Z[10]).length();if(this.determinant()<0)W=-W;J.x=Z[12],J.y=Z[13],J.z=Z[14],v0.copy(this);let K=1/W,G=1/Y,E=1/X;return v0.elements[0]*=K,v0.elements[1]*=K,v0.elements[2]*=K,v0.elements[4]*=G,v0.elements[5]*=G,v0.elements[6]*=G,v0.elements[8]*=E,v0.elements[9]*=E,v0.elements[10]*=E,$.setFromRotationMatrix(v0),Q.x=W,Q.y=Y,Q.z=X,this}makePerspective(J,$,Q,Z,W,Y,X=2000){let H=this.elements,K=2*W/($-J),G=2*W/(Q-Z),E=($+J)/($-J),U=(Q+Z)/(Q-Z),q,D;if(X===2000)q=-(Y+W)/(Y-W),D=-2*Y*W/(Y-W);else if(X===2001)q=-Y/(Y-W),D=-Y*W/(Y-W);else throw Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+X);return H[0]=K,H[4]=0,H[8]=E,H[12]=0,H[1]=0,H[5]=G,H[9]=U,H[13]=0,H[2]=0,H[6]=0,H[10]=q,H[14]=D,H[3]=0,H[7]=0,H[11]=-1,H[15]=0,this}makeOrthographic(J,$,Q,Z,W,Y,X=2000){let H=this.elements,K=1/($-J),G=1/(Q-Z),E=1/(Y-W),U=($+J)*K,q=(Q+Z)*G,D,N;if(X===2000)D=(Y+W)*E,N=-2*E;else if(X===2001)D=W*E,N=-1*E;else throw Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+X);return H[0]=2*K,H[4]=0,H[8]=0,H[12]=-U,H[1]=0,H[5]=2*G,H[9]=0,H[13]=-q,H[2]=0,H[6]=0,H[10]=N,H[14]=-D,H[3]=0,H[7]=0,H[11]=0,H[15]=1,this}equals(J){let $=this.elements,Q=J.elements;for(let Z=0;Z<16;Z++)if($[Z]!==Q[Z])return!1;return!0}fromArray(J,$=0){for(let Q=0;Q<16;Q++)this.elements[Q]=J[Q+$];return this}toArray(J=[],$=0){let Q=this.elements;return J[$]=Q[0],J[$+1]=Q[1],J[$+2]=Q[2],J[$+3]=Q[3],J[$+4]=Q[4],J[$+5]=Q[5],J[$+6]=Q[6],J[$+7]=Q[7],J[$+8]=Q[8],J[$+9]=Q[9],J[$+10]=Q[10],J[$+11]=Q[11],J[$+12]=Q[12],J[$+13]=Q[13],J[$+14]=Q[14],J[$+15]=Q[15],J}}var _6=new v,v0=new Z0,W5=new v(0,0,0),Y5=new v(1,1,1),Q6=new v,N7=new v,w0=new v,N9=new Z0,O9=new M6;class o0{constructor(J=0,$=0,Q=0,Z=o0.DEFAULT_ORDER){this.isEuler=!0,this._x=J,this._y=$,this._z=Q,this._order=Z}get x(){return this._x}set x(J){this._x=J,this._onChangeCallback()}get y(){return this._y}set y(J){this._y=J,this._onChangeCallback()}get z(){return this._z}set z(J){this._z=J,this._onChangeCallback()}get order(){return this._order}set order(J){this._order=J,this._onChangeCallback()}set(J,$,Q,Z=this._order){return this._x=J,this._y=$,this._z=Q,this._order=Z,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(J){return this._x=J._x,this._y=J._y,this._z=J._z,this._order=J._order,this._onChangeCallback(),this}setFromRotationMatrix(J,$=this._order,Q=!0){let Z=J.elements,W=Z[0],Y=Z[4],X=Z[8],H=Z[1],K=Z[5],G=Z[9],E=Z[2],U=Z[6],q=Z[10];switch($){case"XYZ":if(this._y=Math.asin(z0(X,-1,1)),Math.abs(X)<0.9999999)this._x=Math.atan2(-G,q),this._z=Math.atan2(-Y,W);else this._x=Math.atan2(U,K),this._z=0;break;case"YXZ":if(this._x=Math.asin(-z0(G,-1,1)),Math.abs(G)<0.9999999)this._y=Math.atan2(X,q),this._z=Math.atan2(H,K);else this._y=Math.atan2(-E,W),this._z=0;break;case"ZXY":if(this._x=Math.asin(z0(U,-1,1)),Math.abs(U)<0.9999999)this._y=Math.atan2(-E,q),this._z=Math.atan2(-Y,K);else this._y=0,this._z=Math.atan2(H,W);break;case"ZYX":if(this._y=Math.asin(-z0(E,-1,1)),Math.abs(E)<0.9999999)this._x=Math.atan2(U,q),this._z=Math.atan2(H,W);else this._x=0,this._z=Math.atan2(-Y,K);break;case"YZX":if(this._z=Math.asin(z0(H,-1,1)),Math.abs(H)<0.9999999)this._x=Math.atan2(-G,K),this._y=Math.atan2(-E,W);else this._x=0,this._y=Math.atan2(X,q);break;case"XZY":if(this._z=Math.asin(-z0(Y,-1,1)),Math.abs(Y)<0.9999999)this._x=Math.atan2(U,K),this._y=Math.atan2(X,W);else this._x=Math.atan2(-G,q),this._y=0;break;default:console.warn("THREE.Euler: .setFromRotationMatrix() encountered an unknown order: "+$)}if(this._order=$,Q===!0)this._onChangeCallback();return this}setFromQuaternion(J,$,Q){return N9.makeRotationFromQuaternion(J),this.setFromRotationMatrix(N9,$,Q)}setFromVector3(J,$=this._order){return this.set(J.x,J.y,J.z,$)}reorder(J){return O9.setFromEuler(this),this.setFromQuaternion(O9,J)}equals(J){return J._x===this._x&&J._y===this._y&&J._z===this._z&&J._order===this._order}fromArray(J){if(this._x=J[0],this._y=J[1],this._z=J[2],J[3]!==void 0)this._order=J[3];return this._onChangeCallback(),this}toArray(J=[],$=0){return J[$]=this._x,J[$+1]=this._y,J[$+2]=this._z,J[$+3]=this._order,J}_onChange(J){return this._onChangeCallback=J,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}}o0.DEFAULT_ORDER="XYZ";class p8{constructor(){this.mask=1}set(J){this.mask=(1<<J|0)>>>0}enable(J){this.mask|=1<<J|0}enableAll(){this.mask=-1}toggle(J){this.mask^=1<<J|0}disable(J){this.mask&=~(1<<J|0)}disableAll(){this.mask=0}test(J){return(this.mask&J.mask)!==0}isEnabled(J){return(this.mask&(1<<J|0))!==0}}var H5=0,M9=new v,C6=new M6,d0=new Z0,O7=new v,r6=new v,X5=new v,K5=new M6,B9=new v(1,0,0),z9=new v(0,1,0),k9=new v(0,0,1),A9={type:"added"},G5={type:"removed"},P6={type:"childadded",child:null},E8={type:"childremoved",child:null};class R0 extends O6{constructor(){super();this.isObject3D=!0,Object.defineProperty(this,"id",{value:H5++}),this.uuid=H6(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=R0.DEFAULT_UP.clone();let J=new v,$=new o0,Q=new M6,Z=new v(1,1,1);function W(){Q.setFromEuler($,!1)}function Y(){$.setFromQuaternion(Q,void 0,!1)}$._onChange(W),Q._onChange(Y),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:J},rotation:{configurable:!0,enumerable:!0,value:$},quaternion:{configurable:!0,enumerable:!0,value:Q},scale:{configurable:!0,enumerable:!0,value:Z},modelViewMatrix:{value:new Z0},normalMatrix:{value:new jJ}}),this.matrix=new Z0,this.matrixWorld=new Z0,this.matrixAutoUpdate=R0.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=R0.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new p8,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.userData={}}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(J){if(this.matrixAutoUpdate)this.updateMatrix();this.matrix.premultiply(J),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(J){return this.quaternion.premultiply(J),this}setRotationFromAxisAngle(J,$){this.quaternion.setFromAxisAngle(J,$)}setRotationFromEuler(J){this.quaternion.setFromEuler(J,!0)}setRotationFromMatrix(J){this.quaternion.setFromRotationMatrix(J)}setRotationFromQuaternion(J){this.quaternion.copy(J)}rotateOnAxis(J,$){return C6.setFromAxisAngle(J,$),this.quaternion.multiply(C6),this}rotateOnWorldAxis(J,$){return C6.setFromAxisAngle(J,$),this.quaternion.premultiply(C6),this}rotateX(J){return this.rotateOnAxis(B9,J)}rotateY(J){return this.rotateOnAxis(z9,J)}rotateZ(J){return this.rotateOnAxis(k9,J)}translateOnAxis(J,$){return M9.copy(J).applyQuaternion(this.quaternion),this.position.add(M9.multiplyScalar($)),this}translateX(J){return this.translateOnAxis(B9,J)}translateY(J){return this.translateOnAxis(z9,J)}translateZ(J){return this.translateOnAxis(k9,J)}localToWorld(J){return this.updateWorldMatrix(!0,!1),J.applyMatrix4(this.matrixWorld)}worldToLocal(J){return this.updateWorldMatrix(!0,!1),J.applyMatrix4(d0.copy(this.matrixWorld).invert())}lookAt(J,$,Q){if(J.isVector3)O7.copy(J);else O7.set(J,$,Q);let Z=this.parent;if(this.updateWorldMatrix(!0,!1),r6.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight)d0.lookAt(r6,O7,this.up);else d0.lookAt(O7,r6,this.up);if(this.quaternion.setFromRotationMatrix(d0),Z)d0.extractRotation(Z.matrixWorld),C6.setFromRotationMatrix(d0),this.quaternion.premultiply(C6.invert())}add(J){if(arguments.length>1){for(let $=0;$<arguments.length;$++)this.add(arguments[$]);return this}if(J===this)return console.error("THREE.Object3D.add: object can't be added as a child of itself.",J),this;if(J&&J.isObject3D)J.removeFromParent(),J.parent=this,this.children.push(J),J.dispatchEvent(A9),P6.child=J,this.dispatchEvent(P6),P6.child=null;else console.error("THREE.Object3D.add: object not an instance of THREE.Object3D.",J);return this}remove(J){if(arguments.length>1){for(let Q=0;Q<arguments.length;Q++)this.remove(arguments[Q]);return this}let $=this.children.indexOf(J);if($!==-1)J.parent=null,this.children.splice($,1),J.dispatchEvent(G5),E8.child=J,this.dispatchEvent(E8),E8.child=null;return this}removeFromParent(){let J=this.parent;if(J!==null)J.remove(this);return this}clear(){return this.remove(...this.children)}attach(J){if(this.updateWorldMatrix(!0,!1),d0.copy(this.matrixWorld).invert(),J.parent!==null)J.parent.updateWorldMatrix(!0,!1),d0.multiply(J.parent.matrixWorld);return J.applyMatrix4(d0),J.removeFromParent(),J.parent=this,this.children.push(J),J.updateWorldMatrix(!1,!0),J.dispatchEvent(A9),P6.child=J,this.dispatchEvent(P6),P6.child=null,this}getObjectById(J){return this.getObjectByProperty("id",J)}getObjectByName(J){return this.getObjectByProperty("name",J)}getObjectByProperty(J,$){if(this[J]===$)return this;for(let Q=0,Z=this.children.length;Q<Z;Q++){let Y=this.children[Q].getObjectByProperty(J,$);if(Y!==void 0)return Y}return}getObjectsByProperty(J,$,Q=[]){if(this[J]===$)Q.push(this);let Z=this.children;for(let W=0,Y=Z.length;W<Y;W++)Z[W].getObjectsByProperty(J,$,Q);return Q}getWorldPosition(J){return this.updateWorldMatrix(!0,!1),J.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(J){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(r6,J,X5),J}getWorldScale(J){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(r6,K5,J),J}getWorldDirection(J){this.updateWorldMatrix(!0,!1);let $=this.matrixWorld.elements;return J.set($[8],$[9],$[10]).normalize()}raycast(){}traverse(J){J(this);let $=this.children;for(let Q=0,Z=$.length;Q<Z;Q++)$[Q].traverse(J)}traverseVisible(J){if(this.visible===!1)return;J(this);let $=this.children;for(let Q=0,Z=$.length;Q<Z;Q++)$[Q].traverseVisible(J)}traverseAncestors(J){let $=this.parent;if($!==null)J($),$.traverseAncestors(J)}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale),this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(J){if(this.matrixAutoUpdate)this.updateMatrix();if(this.matrixWorldNeedsUpdate||J){if(this.matrixWorldAutoUpdate===!0)if(this.parent===null)this.matrixWorld.copy(this.matrix);else this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix);this.matrixWorldNeedsUpdate=!1,J=!0}let $=this.children;for(let Q=0,Z=$.length;Q<Z;Q++)$[Q].updateMatrixWorld(J)}updateWorldMatrix(J,$){let Q=this.parent;if(J===!0&&Q!==null)Q.updateWorldMatrix(!0,!1);if(this.matrixAutoUpdate)this.updateMatrix();if(this.matrixWorldAutoUpdate===!0)if(this.parent===null)this.matrixWorld.copy(this.matrix);else this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix);if($===!0){let Z=this.children;for(let W=0,Y=Z.length;W<Y;W++)Z[W].updateWorldMatrix(!1,!0)}}toJSON(J){let $=J===void 0||typeof J==="string",Q={};if($)J={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},Q.metadata={version:4.6,type:"Object",generator:"Object3D.toJSON"};let Z={};if(Z.uuid=this.uuid,Z.type=this.type,this.name!=="")Z.name=this.name;if(this.castShadow===!0)Z.castShadow=!0;if(this.receiveShadow===!0)Z.receiveShadow=!0;if(this.visible===!1)Z.visible=!1;if(this.frustumCulled===!1)Z.frustumCulled=!1;if(this.renderOrder!==0)Z.renderOrder=this.renderOrder;if(Object.keys(this.userData).length>0)Z.userData=this.userData;if(Z.layers=this.layers.mask,Z.matrix=this.matrix.toArray(),Z.up=this.up.toArray(),this.matrixAutoUpdate===!1)Z.matrixAutoUpdate=!1;if(this.isInstancedMesh){if(Z.type="InstancedMesh",Z.count=this.count,Z.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null)Z.instanceColor=this.instanceColor.toJSON()}if(this.isBatchedMesh){if(Z.type="BatchedMesh",Z.perObjectFrustumCulled=this.perObjectFrustumCulled,Z.sortObjects=this.sortObjects,Z.drawRanges=this._drawRanges,Z.reservedRanges=this._reservedRanges,Z.visibility=this._visibility,Z.active=this._active,Z.bounds=this._bounds.map((X)=>({boxInitialized:X.boxInitialized,boxMin:X.box.min.toArray(),boxMax:X.box.max.toArray(),sphereInitialized:X.sphereInitialized,sphereRadius:X.sphere.radius,sphereCenter:X.sphere.center.toArray()})),Z.maxInstanceCount=this._maxInstanceCount,Z.maxVertexCount=this._maxVertexCount,Z.maxIndexCount=this._maxIndexCount,Z.geometryInitialized=this._geometryInitialized,Z.geometryCount=this._geometryCount,Z.matricesTexture=this._matricesTexture.toJSON(J),this._colorsTexture!==null)Z.colorsTexture=this._colorsTexture.toJSON(J);if(this.boundingSphere!==null)Z.boundingSphere={center:Z.boundingSphere.center.toArray(),radius:Z.boundingSphere.radius};if(this.boundingBox!==null)Z.boundingBox={min:Z.boundingBox.min.toArray(),max:Z.boundingBox.max.toArray()}}function W(X,H){if(X[H.uuid]===void 0)X[H.uuid]=H.toJSON(J);return H.uuid}if(this.isScene){if(this.background){if(this.background.isColor)Z.background=this.background.toJSON();else if(this.background.isTexture)Z.background=this.background.toJSON(J).uuid}if(this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0)Z.environment=this.environment.toJSON(J).uuid}else if(this.isMesh||this.isLine||this.isPoints){Z.geometry=W(J.geometries,this.geometry);let X=this.geometry.parameters;if(X!==void 0&&X.shapes!==void 0){let H=X.shapes;if(Array.isArray(H))for(let K=0,G=H.length;K<G;K++){let E=H[K];W(J.shapes,E)}else W(J.shapes,H)}}if(this.isSkinnedMesh){if(Z.bindMode=this.bindMode,Z.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0)W(J.skeletons,this.skeleton),Z.skeleton=this.skeleton.uuid}if(this.material!==void 0)if(Array.isArray(this.material)){let X=[];for(let H=0,K=this.material.length;H<K;H++)X.push(W(J.materials,this.material[H]));Z.material=X}else Z.material=W(J.materials,this.material);if(this.children.length>0){Z.children=[];for(let X=0;X<this.children.length;X++)Z.children.push(this.children[X].toJSON(J).object)}if(this.animations.length>0){Z.animations=[];for(let X=0;X<this.animations.length;X++){let H=this.animations[X];Z.animations.push(W(J.animations,H))}}if($){let X=Y(J.geometries),H=Y(J.materials),K=Y(J.textures),G=Y(J.images),E=Y(J.shapes),U=Y(J.skeletons),q=Y(J.animations),D=Y(J.nodes);if(X.length>0)Q.geometries=X;if(H.length>0)Q.materials=H;if(K.length>0)Q.textures=K;if(G.length>0)Q.images=G;if(E.length>0)Q.shapes=E;if(U.length>0)Q.skeletons=U;if(q.length>0)Q.animations=q;if(D.length>0)Q.nodes=D}return Q.object=Z,Q;function Y(X){let H=[];for(let K in X){let G=X[K];delete G.metadata,H.push(G)}return H}}clone(J){return new this.constructor().copy(this,J)}copy(J,$=!0){if(this.name=J.name,this.up.copy(J.up),this.position.copy(J.position),this.rotation.order=J.rotation.order,this.quaternion.copy(J.quaternion),this.scale.copy(J.scale),this.matrix.copy(J.matrix),this.matrixWorld.copy(J.matrixWorld),this.matrixAutoUpdate=J.matrixAutoUpdate,this.matrixWorldAutoUpdate=J.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=J.matrixWorldNeedsUpdate,this.layers.mask=J.layers.mask,this.visible=J.visible,this.castShadow=J.castShadow,this.receiveShadow=J.receiveShadow,this.frustumCulled=J.frustumCulled,this.renderOrder=J.renderOrder,this.animations=J.animations.slice(),this.userData=JSON.parse(JSON.stringify(J.userData)),$===!0)for(let Q=0;Q<J.children.length;Q++){let Z=J.children[Q];this.add(Z.clone())}return this}}R0.DEFAULT_UP=new v(0,1,0);R0.DEFAULT_MATRIX_AUTO_UPDATE=!0;R0.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;var j0=new v,c0=new v,V8=new v,n0=new v,T6=new v,I6=new v,w9=new v,F8=new v,D8=new v,R8=new v,N8=new H0,O8=new H0,M8=new H0;class _0{constructor(J=new v,$=new v,Q=new v){this.a=J,this.b=$,this.c=Q}static getNormal(J,$,Q,Z){Z.subVectors(Q,$),j0.subVectors(J,$),Z.cross(j0);let W=Z.lengthSq();if(W>0)return Z.multiplyScalar(1/Math.sqrt(W));return Z.set(0,0,0)}static getBarycoord(J,$,Q,Z,W){j0.subVectors(Z,$),c0.subVectors(Q,$),V8.subVectors(J,$);let Y=j0.dot(j0),X=j0.dot(c0),H=j0.dot(V8),K=c0.dot(c0),G=c0.dot(V8),E=Y*K-X*X;if(E===0)return W.set(0,0,0),null;let U=1/E,q=(K*H-X*G)*U,D=(Y*G-X*H)*U;return W.set(1-q-D,D,q)}static containsPoint(J,$,Q,Z){if(this.getBarycoord(J,$,Q,Z,n0)===null)return!1;return n0.x>=0&&n0.y>=0&&n0.x+n0.y<=1}static getInterpolation(J,$,Q,Z,W,Y,X,H){if(this.getBarycoord(J,$,Q,Z,n0)===null){if(H.x=0,H.y=0,"z"in H)H.z=0;if("w"in H)H.w=0;return null}return H.setScalar(0),H.addScaledVector(W,n0.x),H.addScaledVector(Y,n0.y),H.addScaledVector(X,n0.z),H}static getInterpolatedAttribute(J,$,Q,Z,W,Y){return N8.setScalar(0),O8.setScalar(0),M8.setScalar(0),N8.fromBufferAttribute(J,$),O8.fromBufferAttribute(J,Q),M8.fromBufferAttribute(J,Z),Y.setScalar(0),Y.addScaledVector(N8,W.x),Y.addScaledVector(O8,W.y),Y.addScaledVector(M8,W.z),Y}static isFrontFacing(J,$,Q,Z){return j0.subVectors(Q,$),c0.subVectors(J,$),j0.cross(c0).dot(Z)<0?!0:!1}set(J,$,Q){return this.a.copy(J),this.b.copy($),this.c.copy(Q),this}setFromPointsAndIndices(J,$,Q,Z){return this.a.copy(J[$]),this.b.copy(J[Q]),this.c.copy(J[Z]),this}setFromAttributeAndIndices(J,$,Q,Z){return this.a.fromBufferAttribute(J,$),this.b.fromBufferAttribute(J,Q),this.c.fromBufferAttribute(J,Z),this}clone(){return new this.constructor().copy(this)}copy(J){return this.a.copy(J.a),this.b.copy(J.b),this.c.copy(J.c),this}getArea(){return j0.subVectors(this.c,this.b),c0.subVectors(this.a,this.b),j0.cross(c0).length()*0.5}getMidpoint(J){return J.addVectors(this.a,this.b).add(this.c).multiplyScalar(0.3333333333333333)}getNormal(J){return _0.getNormal(this.a,this.b,this.c,J)}getPlane(J){return J.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(J,$){return _0.getBarycoord(J,this.a,this.b,this.c,$)}getInterpolation(J,$,Q,Z,W){return _0.getInterpolation(J,this.a,this.b,this.c,$,Q,Z,W)}containsPoint(J){return _0.containsPoint(J,this.a,this.b,this.c)}isFrontFacing(J){return _0.isFrontFacing(this.a,this.b,this.c,J)}intersectsBox(J){return J.intersectsTriangle(this)}closestPointToPoint(J,$){let Q=this.a,Z=this.b,W=this.c,Y,X;T6.subVectors(Z,Q),I6.subVectors(W,Q),F8.subVectors(J,Q);let H=T6.dot(F8),K=I6.dot(F8);if(H<=0&&K<=0)return $.copy(Q);D8.subVectors(J,Z);let G=T6.dot(D8),E=I6.dot(D8);if(G>=0&&E<=G)return $.copy(Z);let U=H*E-G*K;if(U<=0&&H>=0&&G<=0)return Y=H/(H-G),$.copy(Q).addScaledVector(T6,Y);R8.subVectors(J,W);let q=T6.dot(R8),D=I6.dot(R8);if(D>=0&&q<=D)return $.copy(W);let N=q*K-H*D;if(N<=0&&K>=0&&D<=0)return X=K/(K-D),$.copy(Q).addScaledVector(I6,X);let O=G*D-q*E;if(O<=0&&E-G>=0&&q-D>=0)return w9.subVectors(W,Z),X=(E-G)/(E-G+(q-D)),$.copy(Z).addScaledVector(w9,X);let V=1/(O+N+U);return Y=N*V,X=U*V,$.copy(Q).addScaledVector(T6,Y).addScaledVector(I6,X)}equals(J){return J.a.equals(this.a)&&J.b.equals(this.b)&&J.c.equals(this.c)}}var V$={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},Z6={h:0,s:0,l:0},M7={h:0,s:0,l:0};function B8(J,$,Q){if(Q<0)Q+=1;if(Q>1)Q-=1;if(Q<0.16666666666666666)return J+($-J)*6*Q;if(Q<0.5)return $;if(Q<0.6666666666666666)return J+($-J)*6*(0.6666666666666666-Q);return J}class nJ{constructor(J,$,Q){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(J,$,Q)}set(J,$,Q){if($===void 0&&Q===void 0){let Z=J;if(Z&&Z.isColor)this.copy(Z);else if(typeof Z==="number")this.setHex(Z);else if(typeof Z==="string")this.setStyle(Z)}else this.setRGB(J,$,Q);return this}setScalar(J){return this.r=J,this.g=J,this.b=J,this}setHex(J,$="srgb"){return J=Math.floor(J),this.r=(J>>16&255)/255,this.g=(J>>8&255)/255,this.b=(J&255)/255,dJ.toWorkingColorSpace(this,$),this}setRGB(J,$,Q,Z=dJ.workingColorSpace){return this.r=J,this.g=$,this.b=Q,dJ.toWorkingColorSpace(this,Z),this}setHSL(J,$,Q,Z=dJ.workingColorSpace){if(J=a$(J,1),$=z0($,0,1),Q=z0(Q,0,1),$===0)this.r=this.g=this.b=Q;else{let W=Q<=0.5?Q*(1+$):Q+$-Q*$,Y=2*Q-W;this.r=B8(Y,W,J+0.3333333333333333),this.g=B8(Y,W,J),this.b=B8(Y,W,J-0.3333333333333333)}return dJ.toWorkingColorSpace(this,Z),this}setStyle(J,$="srgb"){function Q(W){if(W===void 0)return;if(parseFloat(W)<1)console.warn("THREE.Color: Alpha component of "+J+" will be ignored.")}let Z;if(Z=/^(\w+)\(([^\)]*)\)/.exec(J)){let W,Y=Z[1],X=Z[2];switch(Y){case"rgb":case"rgba":if(W=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(X))return Q(W[4]),this.setRGB(Math.min(255,parseInt(W[1],10))/255,Math.min(255,parseInt(W[2],10))/255,Math.min(255,parseInt(W[3],10))/255,$);if(W=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(X))return Q(W[4]),this.setRGB(Math.min(100,parseInt(W[1],10))/100,Math.min(100,parseInt(W[2],10))/100,Math.min(100,parseInt(W[3],10))/100,$);break;case"hsl":case"hsla":if(W=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(X))return Q(W[4]),this.setHSL(parseFloat(W[1])/360,parseFloat(W[2])/100,parseFloat(W[3])/100,$);break;default:console.warn("THREE.Color: Unknown color model "+J)}}else if(Z=/^\#([A-Fa-f\d]+)$/.exec(J)){let W=Z[1],Y=W.length;if(Y===3)return this.setRGB(parseInt(W.charAt(0),16)/15,parseInt(W.charAt(1),16)/15,parseInt(W.charAt(2),16)/15,$);else if(Y===6)return this.setHex(parseInt(W,16),$);else console.warn("THREE.Color: Invalid hex color "+J)}else if(J&&J.length>0)return this.setColorName(J,$);return this}setColorName(J,$="srgb"){let Q=V$[J.toLowerCase()];if(Q!==void 0)this.setHex(Q,$);else console.warn("THREE.Color: Unknown color "+J);return this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(J){return this.r=J.r,this.g=J.g,this.b=J.b,this}copySRGBToLinear(J){return this.r=i0(J.r),this.g=i0(J.g),this.b=i0(J.b),this}copyLinearToSRGB(J){return this.r=g6(J.r),this.g=g6(J.g),this.b=g6(J.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(J="srgb"){return dJ.fromWorkingColorSpace(D0.copy(this),J),Math.round(z0(D0.r*255,0,255))*65536+Math.round(z0(D0.g*255,0,255))*256+Math.round(z0(D0.b*255,0,255))}getHexString(J="srgb"){return("000000"+this.getHex(J).toString(16)).slice(-6)}getHSL(J,$=dJ.workingColorSpace){dJ.fromWorkingColorSpace(D0.copy(this),$);let{r:Q,g:Z,b:W}=D0,Y=Math.max(Q,Z,W),X=Math.min(Q,Z,W),H,K,G=(X+Y)/2;if(X===Y)H=0,K=0;else{let E=Y-X;switch(K=G<=0.5?E/(Y+X):E/(2-Y-X),Y){case Q:H=(Z-W)/E+(Z<W?6:0);break;case Z:H=(W-Q)/E+2;break;case W:H=(Q-Z)/E+4;break}H/=6}return J.h=H,J.s=K,J.l=G,J}getRGB(J,$=dJ.workingColorSpace){return dJ.fromWorkingColorSpace(D0.copy(this),$),J.r=D0.r,J.g=D0.g,J.b=D0.b,J}getStyle(J="srgb"){dJ.fromWorkingColorSpace(D0.copy(this),J);let{r:$,g:Q,b:Z}=D0;if(J!=="srgb")return`color(${J} ${$.toFixed(3)} ${Q.toFixed(3)} ${Z.toFixed(3)})`;return`rgb(${Math.round($*255)},${Math.round(Q*255)},${Math.round(Z*255)})`}offsetHSL(J,$,Q){return this.getHSL(Z6),this.setHSL(Z6.h+J,Z6.s+$,Z6.l+Q)}add(J){return this.r+=J.r,this.g+=J.g,this.b+=J.b,this}addColors(J,$){return this.r=J.r+$.r,this.g=J.g+$.g,this.b=J.b+$.b,this}addScalar(J){return this.r+=J,this.g+=J,this.b+=J,this}sub(J){return this.r=Math.max(0,this.r-J.r),this.g=Math.max(0,this.g-J.g),this.b=Math.max(0,this.b-J.b),this}multiply(J){return this.r*=J.r,this.g*=J.g,this.b*=J.b,this}multiplyScalar(J){return this.r*=J,this.g*=J,this.b*=J,this}lerp(J,$){return this.r+=(J.r-this.r)*$,this.g+=(J.g-this.g)*$,this.b+=(J.b-this.b)*$,this}lerpColors(J,$,Q){return this.r=J.r+($.r-J.r)*Q,this.g=J.g+($.g-J.g)*Q,this.b=J.b+($.b-J.b)*Q,this}lerpHSL(J,$){this.getHSL(Z6),J.getHSL(M7);let Q=Z8(Z6.h,M7.h,$),Z=Z8(Z6.s,M7.s,$),W=Z8(Z6.l,M7.l,$);return this.setHSL(Q,Z,W),this}setFromVector3(J){return this.r=J.x,this.g=J.y,this.b=J.z,this}applyMatrix3(J){let $=this.r,Q=this.g,Z=this.b,W=J.elements;return this.r=W[0]*$+W[3]*Q+W[6]*Z,this.g=W[1]*$+W[4]*Q+W[7]*Z,this.b=W[2]*$+W[5]*Q+W[8]*Z,this}equals(J){return J.r===this.r&&J.g===this.g&&J.b===this.b}fromArray(J,$=0){return this.r=J[$],this.g=J[$+1],this.b=J[$+2],this}toArray(J=[],$=0){return J[$]=this.r,J[$+1]=this.g,J[$+2]=this.b,J}fromBufferAttribute(J,$){return this.r=J.getX($),this.g=J.getY($),this.b=J.getZ($),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}}var D0=new nJ;nJ.NAMES=V$;var U5=0;class K6 extends O6{static get type(){return"Material"}get type(){return this.constructor.type}set type(J){}constructor(){super();this.isMaterial=!0,Object.defineProperty(this,"id",{value:U5++}),this.uuid=H6(),this.name="",this.blending=1,this.side=0,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=204,this.blendDst=205,this.blendEquation=100,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new nJ(0,0,0),this.blendAlpha=0,this.depthFunc=3,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=519,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=7680,this.stencilZFail=7680,this.stencilZPass=7680,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(J){if(this._alphaTest>0!==J>0)this.version++;this._alphaTest=J}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(J){if(J===void 0)return;for(let $ in J){let Q=J[$];if(Q===void 0){console.warn(`THREE.Material: parameter '${$}' has value of undefined.`);continue}let Z=this[$];if(Z===void 0){console.warn(`THREE.Material: '${$}' is not a property of THREE.${this.type}.`);continue}if(Z&&Z.isColor)Z.set(Q);else if(Z&&Z.isVector3&&(Q&&Q.isVector3))Z.copy(Q);else this[$]=Q}}toJSON(J){let $=J===void 0||typeof J==="string";if($)J={textures:{},images:{}};let Q={metadata:{version:4.6,type:"Material",generator:"Material.toJSON"}};if(Q.uuid=this.uuid,Q.type=this.type,this.name!=="")Q.name=this.name;if(this.color&&this.color.isColor)Q.color=this.color.getHex();if(this.roughness!==void 0)Q.roughness=this.roughness;if(this.metalness!==void 0)Q.metalness=this.metalness;if(this.sheen!==void 0)Q.sheen=this.sheen;if(this.sheenColor&&this.sheenColor.isColor)Q.sheenColor=this.sheenColor.getHex();if(this.sheenRoughness!==void 0)Q.sheenRoughness=this.sheenRoughness;if(this.emissive&&this.emissive.isColor)Q.emissive=this.emissive.getHex();if(this.emissiveIntensity!==void 0&&this.emissiveIntensity!==1)Q.emissiveIntensity=this.emissiveIntensity;if(this.specular&&this.specular.isColor)Q.specular=this.specular.getHex();if(this.specularIntensity!==void 0)Q.specularIntensity=this.specularIntensity;if(this.specularColor&&this.specularColor.isColor)Q.specularColor=this.specularColor.getHex();if(this.shininess!==void 0)Q.shininess=this.shininess;if(this.clearcoat!==void 0)Q.clearcoat=this.clearcoat;if(this.clearcoatRoughness!==void 0)Q.clearcoatRoughness=this.clearcoatRoughness;if(this.clearcoatMap&&this.clearcoatMap.isTexture)Q.clearcoatMap=this.clearcoatMap.toJSON(J).uuid;if(this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture)Q.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(J).uuid;if(this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture)Q.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(J).uuid,Q.clearcoatNormalScale=this.clearcoatNormalScale.toArray();if(this.dispersion!==void 0)Q.dispersion=this.dispersion;if(this.iridescence!==void 0)Q.iridescence=this.iridescence;if(this.iridescenceIOR!==void 0)Q.iridescenceIOR=this.iridescenceIOR;if(this.iridescenceThicknessRange!==void 0)Q.iridescenceThicknessRange=this.iridescenceThicknessRange;if(this.iridescenceMap&&this.iridescenceMap.isTexture)Q.iridescenceMap=this.iridescenceMap.toJSON(J).uuid;if(this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture)Q.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(J).uuid;if(this.anisotropy!==void 0)Q.anisotropy=this.anisotropy;if(this.anisotropyRotation!==void 0)Q.anisotropyRotation=this.anisotropyRotation;if(this.anisotropyMap&&this.anisotropyMap.isTexture)Q.anisotropyMap=this.anisotropyMap.toJSON(J).uuid;if(this.map&&this.map.isTexture)Q.map=this.map.toJSON(J).uuid;if(this.matcap&&this.matcap.isTexture)Q.matcap=this.matcap.toJSON(J).uuid;if(this.alphaMap&&this.alphaMap.isTexture)Q.alphaMap=this.alphaMap.toJSON(J).uuid;if(this.lightMap&&this.lightMap.isTexture)Q.lightMap=this.lightMap.toJSON(J).uuid,Q.lightMapIntensity=this.lightMapIntensity;if(this.aoMap&&this.aoMap.isTexture)Q.aoMap=this.aoMap.toJSON(J).uuid,Q.aoMapIntensity=this.aoMapIntensity;if(this.bumpMap&&this.bumpMap.isTexture)Q.bumpMap=this.bumpMap.toJSON(J).uuid,Q.bumpScale=this.bumpScale;if(this.normalMap&&this.normalMap.isTexture)Q.normalMap=this.normalMap.toJSON(J).uuid,Q.normalMapType=this.normalMapType,Q.normalScale=this.normalScale.toArray();if(this.displacementMap&&this.displacementMap.isTexture)Q.displacementMap=this.displacementMap.toJSON(J).uuid,Q.displacementScale=this.displacementScale,Q.displacementBias=this.displacementBias;if(this.roughnessMap&&this.roughnessMap.isTexture)Q.roughnessMap=this.roughnessMap.toJSON(J).uuid;if(this.metalnessMap&&this.metalnessMap.isTexture)Q.metalnessMap=this.metalnessMap.toJSON(J).uuid;if(this.emissiveMap&&this.emissiveMap.isTexture)Q.emissiveMap=this.emissiveMap.toJSON(J).uuid;if(this.specularMap&&this.specularMap.isTexture)Q.specularMap=this.specularMap.toJSON(J).uuid;if(this.specularIntensityMap&&this.specularIntensityMap.isTexture)Q.specularIntensityMap=this.specularIntensityMap.toJSON(J).uuid;if(this.specularColorMap&&this.specularColorMap.isTexture)Q.specularColorMap=this.specularColorMap.toJSON(J).uuid;if(this.envMap&&this.envMap.isTexture){if(Q.envMap=this.envMap.toJSON(J).uuid,this.combine!==void 0)Q.combine=this.combine}if(this.envMapRotation!==void 0)Q.envMapRotation=this.envMapRotation.toArray();if(this.envMapIntensity!==void 0)Q.envMapIntensity=this.envMapIntensity;if(this.reflectivity!==void 0)Q.reflectivity=this.reflectivity;if(this.refractionRatio!==void 0)Q.refractionRatio=this.refractionRatio;if(this.gradientMap&&this.gradientMap.isTexture)Q.gradientMap=this.gradientMap.toJSON(J).uuid;if(this.transmission!==void 0)Q.transmission=this.transmission;if(this.transmissionMap&&this.transmissionMap.isTexture)Q.transmissionMap=this.transmissionMap.toJSON(J).uuid;if(this.thickness!==void 0)Q.thickness=this.thickness;if(this.thicknessMap&&this.thicknessMap.isTexture)Q.thicknessMap=this.thicknessMap.toJSON(J).uuid;if(this.attenuationDistance!==void 0&&this.attenuationDistance!==1/0)Q.attenuationDistance=this.attenuationDistance;if(this.attenuationColor!==void 0)Q.attenuationColor=this.attenuationColor.getHex();if(this.size!==void 0)Q.size=this.size;if(this.shadowSide!==null)Q.shadowSide=this.shadowSide;if(this.sizeAttenuation!==void 0)Q.sizeAttenuation=this.sizeAttenuation;if(this.blending!==1)Q.blending=this.blending;if(this.side!==0)Q.side=this.side;if(this.vertexColors===!0)Q.vertexColors=!0;if(this.opacity<1)Q.opacity=this.opacity;if(this.transparent===!0)Q.transparent=!0;if(this.blendSrc!==204)Q.blendSrc=this.blendSrc;if(this.blendDst!==205)Q.blendDst=this.blendDst;if(this.blendEquation!==100)Q.blendEquation=this.blendEquation;if(this.blendSrcAlpha!==null)Q.blendSrcAlpha=this.blendSrcAlpha;if(this.blendDstAlpha!==null)Q.blendDstAlpha=this.blendDstAlpha;if(this.blendEquationAlpha!==null)Q.blendEquationAlpha=this.blendEquationAlpha;if(this.blendColor&&this.blendColor.isColor)Q.blendColor=this.blendColor.getHex();if(this.blendAlpha!==0)Q.blendAlpha=this.blendAlpha;if(this.depthFunc!==3)Q.depthFunc=this.depthFunc;if(this.depthTest===!1)Q.depthTest=this.depthTest;if(this.depthWrite===!1)Q.depthWrite=this.depthWrite;if(this.colorWrite===!1)Q.colorWrite=this.colorWrite;if(this.stencilWriteMask!==255)Q.stencilWriteMask=this.stencilWriteMask;if(this.stencilFunc!==519)Q.stencilFunc=this.stencilFunc;if(this.stencilRef!==0)Q.stencilRef=this.stencilRef;if(this.stencilFuncMask!==255)Q.stencilFuncMask=this.stencilFuncMask;if(this.stencilFail!==7680)Q.stencilFail=this.stencilFail;if(this.stencilZFail!==7680)Q.stencilZFail=this.stencilZFail;if(this.stencilZPass!==7680)Q.stencilZPass=this.stencilZPass;if(this.stencilWrite===!0)Q.stencilWrite=this.stencilWrite;if(this.rotation!==void 0&&this.rotation!==0)Q.rotation=this.rotation;if(this.polygonOffset===!0)Q.polygonOffset=!0;if(this.polygonOffsetFactor!==0)Q.polygonOffsetFactor=this.polygonOffsetFactor;if(this.polygonOffsetUnits!==0)Q.polygonOffsetUnits=this.polygonOffsetUnits;if(this.linewidth!==void 0&&this.linewidth!==1)Q.linewidth=this.linewidth;if(this.dashSize!==void 0)Q.dashSize=this.dashSize;if(this.gapSize!==void 0)Q.gapSize=this.gapSize;if(this.scale!==void 0)Q.scale=this.scale;if(this.dithering===!0)Q.dithering=!0;if(this.alphaTest>0)Q.alphaTest=this.alphaTest;if(this.alphaHash===!0)Q.alphaHash=!0;if(this.alphaToCoverage===!0)Q.alphaToCoverage=!0;if(this.premultipliedAlpha===!0)Q.premultipliedAlpha=!0;if(this.forceSinglePass===!0)Q.forceSinglePass=!0;if(this.wireframe===!0)Q.wireframe=!0;if(this.wireframeLinewidth>1)Q.wireframeLinewidth=this.wireframeLinewidth;if(this.wireframeLinecap!=="round")Q.wireframeLinecap=this.wireframeLinecap;if(this.wireframeLinejoin!=="round")Q.wireframeLinejoin=this.wireframeLinejoin;if(this.flatShading===!0)Q.flatShading=!0;if(this.visible===!1)Q.visible=!1;if(this.toneMapped===!1)Q.toneMapped=!1;if(this.fog===!1)Q.fog=!1;if(Object.keys(this.userData).length>0)Q.userData=this.userData;function Z(W){let Y=[];for(let X in W){let H=W[X];delete H.metadata,Y.push(H)}return Y}if($){let W=Z(J.textures),Y=Z(J.images);if(W.length>0)Q.textures=W;if(Y.length>0)Q.images=Y}return Q}clone(){return new this.constructor().copy(this)}copy(J){this.name=J.name,this.blending=J.blending,this.side=J.side,this.vertexColors=J.vertexColors,this.opacity=J.opacity,this.transparent=J.transparent,this.blendSrc=J.blendSrc,this.blendDst=J.blendDst,this.blendEquation=J.blendEquation,this.blendSrcAlpha=J.blendSrcAlpha,this.blendDstAlpha=J.blendDstAlpha,this.blendEquationAlpha=J.blendEquationAlpha,this.blendColor.copy(J.blendColor),this.blendAlpha=J.blendAlpha,this.depthFunc=J.depthFunc,this.depthTest=J.depthTest,this.depthWrite=J.depthWrite,this.stencilWriteMask=J.stencilWriteMask,this.stencilFunc=J.stencilFunc,this.stencilRef=J.stencilRef,this.stencilFuncMask=J.stencilFuncMask,this.stencilFail=J.stencilFail,this.stencilZFail=J.stencilZFail,this.stencilZPass=J.stencilZPass,this.stencilWrite=J.stencilWrite;let $=J.clippingPlanes,Q=null;if($!==null){let Z=$.length;Q=Array(Z);for(let W=0;W!==Z;++W)Q[W]=$[W].clone()}return this.clippingPlanes=Q,this.clipIntersection=J.clipIntersection,this.clipShadows=J.clipShadows,this.shadowSide=J.shadowSide,this.colorWrite=J.colorWrite,this.precision=J.precision,this.polygonOffset=J.polygonOffset,this.polygonOffsetFactor=J.polygonOffsetFactor,this.polygonOffsetUnits=J.polygonOffsetUnits,this.dithering=J.dithering,this.alphaTest=J.alphaTest,this.alphaHash=J.alphaHash,this.alphaToCoverage=J.alphaToCoverage,this.premultipliedAlpha=J.premultipliedAlpha,this.forceSinglePass=J.forceSinglePass,this.visible=J.visible,this.toneMapped=J.toneMapped,this.userData=JSON.parse(JSON.stringify(J.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(J){if(J===!0)this.version++}onBuild(){console.warn("Material: onBuild() has been removed.")}}class H7 extends K6{static get type(){return"MeshBasicMaterial"}constructor(J){super();this.isMeshBasicMaterial=!0,this.color=new nJ(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new o0,this.combine=0,this.reflectivity=1,this.refractionRatio=0.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(J)}copy(J){return super.copy(J),this.color.copy(J.color),this.map=J.map,this.lightMap=J.lightMap,this.lightMapIntensity=J.lightMapIntensity,this.aoMap=J.aoMap,this.aoMapIntensity=J.aoMapIntensity,this.specularMap=J.specularMap,this.alphaMap=J.alphaMap,this.envMap=J.envMap,this.envMapRotation.copy(J.envMapRotation),this.combine=J.combine,this.reflectivity=J.reflectivity,this.refractionRatio=J.refractionRatio,this.wireframe=J.wireframe,this.wireframeLinewidth=J.wireframeLinewidth,this.wireframeLinecap=J.wireframeLinecap,this.wireframeLinejoin=J.wireframeLinejoin,this.fog=J.fog,this}}var K0=new v,B7=new uJ;class I0{constructor(J,$,Q=!1){if(Array.isArray(J))throw TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,this.name="",this.array=J,this.itemSize=$,this.count=J!==void 0?J.length/$:0,this.normalized=Q,this.usage=35044,this.updateRanges=[],this.gpuType=1015,this.version=0}onUploadCallback(){}set needsUpdate(J){if(J===!0)this.version++}setUsage(J){return this.usage=J,this}addUpdateRange(J,$){this.updateRanges.push({start:J,count:$})}clearUpdateRanges(){this.updateRanges.length=0}copy(J){return this.name=J.name,this.array=new J.array.constructor(J.array),this.itemSize=J.itemSize,this.count=J.count,this.normalized=J.normalized,this.usage=J.usage,this.gpuType=J.gpuType,this}copyAt(J,$,Q){J*=this.itemSize,Q*=$.itemSize;for(let Z=0,W=this.itemSize;Z<W;Z++)this.array[J+Z]=$.array[Q+Z];return this}copyArray(J){return this.array.set(J),this}applyMatrix3(J){if(this.itemSize===2)for(let $=0,Q=this.count;$<Q;$++)B7.fromBufferAttribute(this,$),B7.applyMatrix3(J),this.setXY($,B7.x,B7.y);else if(this.itemSize===3)for(let $=0,Q=this.count;$<Q;$++)K0.fromBufferAttribute(this,$),K0.applyMatrix3(J),this.setXYZ($,K0.x,K0.y,K0.z);return this}applyMatrix4(J){for(let $=0,Q=this.count;$<Q;$++)K0.fromBufferAttribute(this,$),K0.applyMatrix4(J),this.setXYZ($,K0.x,K0.y,K0.z);return this}applyNormalMatrix(J){for(let $=0,Q=this.count;$<Q;$++)K0.fromBufferAttribute(this,$),K0.applyNormalMatrix(J),this.setXYZ($,K0.x,K0.y,K0.z);return this}transformDirection(J){for(let $=0,Q=this.count;$<Q;$++)K0.fromBufferAttribute(this,$),K0.transformDirection(J),this.setXYZ($,K0.x,K0.y,K0.z);return this}set(J,$=0){return this.array.set(J,$),this}getComponent(J,$){let Q=this.array[J*this.itemSize+$];if(this.normalized)Q=x0(Q,this.array);return Q}setComponent(J,$,Q){if(this.normalized)Q=aJ(Q,this.array);return this.array[J*this.itemSize+$]=Q,this}getX(J){let $=this.array[J*this.itemSize];if(this.normalized)$=x0($,this.array);return $}setX(J,$){if(this.normalized)$=aJ($,this.array);return this.array[J*this.itemSize]=$,this}getY(J){let $=this.array[J*this.itemSize+1];if(this.normalized)$=x0($,this.array);return $}setY(J,$){if(this.normalized)$=aJ($,this.array);return this.array[J*this.itemSize+1]=$,this}getZ(J){let $=this.array[J*this.itemSize+2];if(this.normalized)$=x0($,this.array);return $}setZ(J,$){if(this.normalized)$=aJ($,this.array);return this.array[J*this.itemSize+2]=$,this}getW(J){let $=this.array[J*this.itemSize+3];if(this.normalized)$=x0($,this.array);return $}setW(J,$){if(this.normalized)$=aJ($,this.array);return this.array[J*this.itemSize+3]=$,this}setXY(J,$,Q){if(J*=this.itemSize,this.normalized)$=aJ($,this.array),Q=aJ(Q,this.array);return this.array[J+0]=$,this.array[J+1]=Q,this}setXYZ(J,$,Q,Z){if(J*=this.itemSize,this.normalized)$=aJ($,this.array),Q=aJ(Q,this.array),Z=aJ(Z,this.array);return this.array[J+0]=$,this.array[J+1]=Q,this.array[J+2]=Z,this}setXYZW(J,$,Q,Z,W){if(J*=this.itemSize,this.normalized)$=aJ($,this.array),Q=aJ(Q,this.array),Z=aJ(Z,this.array),W=aJ(W,this.array);return this.array[J+0]=$,this.array[J+1]=Q,this.array[J+2]=Z,this.array[J+3]=W,this}onUpload(J){return this.onUploadCallback=J,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){let J={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};if(this.name!=="")J.name=this.name;if(this.usage!==35044)J.usage=this.usage;return J}}class g8 extends I0{constructor(J,$,Q){super(new Uint16Array(J),$,Q)}}class m8 extends I0{constructor(J,$,Q){super(new Uint32Array(J),$,Q)}}class Y0 extends I0{constructor(J,$,Q){super(new Float32Array(J),$,Q)}}var q5=0,P0=new Z0,z8=new R0,S6=new v,L0=new u6,t6=new u6,q0=new v;class V0 extends O6{constructor(){super();this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:q5++}),this.uuid=H6(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={}}getIndex(){return this.index}setIndex(J){if(Array.isArray(J))this.index=new((G$(J))?m8:g8)(J,1);else this.index=J;return this}setIndirect(J){return this.indirect=J,this}getIndirect(){return this.indirect}getAttribute(J){return this.attributes[J]}setAttribute(J,$){return this.attributes[J]=$,this}deleteAttribute(J){return delete this.attributes[J],this}hasAttribute(J){return this.attributes[J]!==void 0}addGroup(J,$,Q=0){this.groups.push({start:J,count:$,materialIndex:Q})}clearGroups(){this.groups=[]}setDrawRange(J,$){this.drawRange.start=J,this.drawRange.count=$}applyMatrix4(J){let $=this.attributes.position;if($!==void 0)$.applyMatrix4(J),$.needsUpdate=!0;let Q=this.attributes.normal;if(Q!==void 0){let W=new jJ().getNormalMatrix(J);Q.applyNormalMatrix(W),Q.needsUpdate=!0}let Z=this.attributes.tangent;if(Z!==void 0)Z.transformDirection(J),Z.needsUpdate=!0;if(this.boundingBox!==null)this.computeBoundingBox();if(this.boundingSphere!==null)this.computeBoundingSphere();return this}applyQuaternion(J){return P0.makeRotationFromQuaternion(J),this.applyMatrix4(P0),this}rotateX(J){return P0.makeRotationX(J),this.applyMatrix4(P0),this}rotateY(J){return P0.makeRotationY(J),this.applyMatrix4(P0),this}rotateZ(J){return P0.makeRotationZ(J),this.applyMatrix4(P0),this}translate(J,$,Q){return P0.makeTranslation(J,$,Q),this.applyMatrix4(P0),this}scale(J,$,Q){return P0.makeScale(J,$,Q),this.applyMatrix4(P0),this}lookAt(J){return z8.lookAt(J),z8.updateMatrix(),this.applyMatrix4(z8.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(S6).negate(),this.translate(S6.x,S6.y,S6.z),this}setFromPoints(J){let $=this.getAttribute("position");if($===void 0){let Q=[];for(let Z=0,W=J.length;Z<W;Z++){let Y=J[Z];Q.push(Y.x,Y.y,Y.z||0)}this.setAttribute("position",new Y0(Q,3))}else{for(let Q=0,Z=$.count;Q<Z;Q++){let W=J[Q];$.setXYZ(Q,W.x,W.y,W.z||0)}if(J.length>$.count)console.warn("THREE.BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry.");$.needsUpdate=!0}return this}computeBoundingBox(){if(this.boundingBox===null)this.boundingBox=new u6;let J=this.attributes.position,$=this.morphAttributes.position;if(J&&J.isGLBufferAttribute){console.error("THREE.BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new v(-1/0,-1/0,-1/0),new v(1/0,1/0,1/0));return}if(J!==void 0){if(this.boundingBox.setFromBufferAttribute(J),$)for(let Q=0,Z=$.length;Q<Z;Q++){let W=$[Q];if(L0.setFromBufferAttribute(W),this.morphTargetsRelative)q0.addVectors(this.boundingBox.min,L0.min),this.boundingBox.expandByPoint(q0),q0.addVectors(this.boundingBox.max,L0.max),this.boundingBox.expandByPoint(q0);else this.boundingBox.expandByPoint(L0.min),this.boundingBox.expandByPoint(L0.max)}}else this.boundingBox.makeEmpty();if(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))console.error('THREE.BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){if(this.boundingSphere===null)this.boundingSphere=new l6;let J=this.attributes.position,$=this.morphAttributes.position;if(J&&J.isGLBufferAttribute){console.error("THREE.BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new v,1/0);return}if(J){let Q=this.boundingSphere.center;if(L0.setFromBufferAttribute(J),$)for(let W=0,Y=$.length;W<Y;W++){let X=$[W];if(t6.setFromBufferAttribute(X),this.morphTargetsRelative)q0.addVectors(L0.min,t6.min),L0.expandByPoint(q0),q0.addVectors(L0.max,t6.max),L0.expandByPoint(q0);else L0.expandByPoint(t6.min),L0.expandByPoint(t6.max)}L0.getCenter(Q);let Z=0;for(let W=0,Y=J.count;W<Y;W++)q0.fromBufferAttribute(J,W),Z=Math.max(Z,Q.distanceToSquared(q0));if($)for(let W=0,Y=$.length;W<Y;W++){let X=$[W],H=this.morphTargetsRelative;for(let K=0,G=X.count;K<G;K++){if(q0.fromBufferAttribute(X,K),H)S6.fromBufferAttribute(J,K),q0.add(S6);Z=Math.max(Z,Q.distanceToSquared(q0))}}if(this.boundingSphere.radius=Math.sqrt(Z),isNaN(this.boundingSphere.radius))console.error('THREE.BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){let J=this.index,$=this.attributes;if(J===null||$.position===void 0||$.normal===void 0||$.uv===void 0){console.error("THREE.BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}let{position:Q,normal:Z,uv:W}=$;if(this.hasAttribute("tangent")===!1)this.setAttribute("tangent",new I0(new Float32Array(4*Q.count),4));let Y=this.getAttribute("tangent"),X=[],H=[];for(let P=0;P<Q.count;P++)X[P]=new v,H[P]=new v;let K=new v,G=new v,E=new v,U=new uJ,q=new uJ,D=new uJ,N=new v,O=new v;function V(P,p,B){K.fromBufferAttribute(Q,P),G.fromBufferAttribute(Q,p),E.fromBufferAttribute(Q,B),U.fromBufferAttribute(W,P),q.fromBufferAttribute(W,p),D.fromBufferAttribute(W,B),G.sub(K),E.sub(K),q.sub(U),D.sub(U);let k=1/(q.x*D.y-D.x*q.y);if(!isFinite(k))return;N.copy(G).multiplyScalar(D.y).addScaledVector(E,-q.y).multiplyScalar(k),O.copy(E).multiplyScalar(q.x).addScaledVector(G,-D.x).multiplyScalar(k),X[P].add(N),X[p].add(N),X[B].add(N),H[P].add(O),H[p].add(O),H[B].add(O)}let F=this.groups;if(F.length===0)F=[{start:0,count:J.count}];for(let P=0,p=F.length;P<p;++P){let B=F[P],k=B.start,T=B.count;for(let x=k,m=k+T;x<m;x+=3)V(J.getX(x+0),J.getX(x+1),J.getX(x+2))}let A=new v,z=new v,_=new v,b=new v;function L(P){_.fromBufferAttribute(Z,P),b.copy(_);let p=X[P];A.copy(p),A.sub(_.multiplyScalar(_.dot(p))).normalize(),z.crossVectors(b,p);let k=z.dot(H[P])<0?-1:1;Y.setXYZW(P,A.x,A.y,A.z,k)}for(let P=0,p=F.length;P<p;++P){let B=F[P],k=B.start,T=B.count;for(let x=k,m=k+T;x<m;x+=3)L(J.getX(x+0)),L(J.getX(x+1)),L(J.getX(x+2))}}computeVertexNormals(){let J=this.index,$=this.getAttribute("position");if($!==void 0){let Q=this.getAttribute("normal");if(Q===void 0)Q=new I0(new Float32Array($.count*3),3),this.setAttribute("normal",Q);else for(let U=0,q=Q.count;U<q;U++)Q.setXYZ(U,0,0,0);let Z=new v,W=new v,Y=new v,X=new v,H=new v,K=new v,G=new v,E=new v;if(J)for(let U=0,q=J.count;U<q;U+=3){let D=J.getX(U+0),N=J.getX(U+1),O=J.getX(U+2);Z.fromBufferAttribute($,D),W.fromBufferAttribute($,N),Y.fromBufferAttribute($,O),G.subVectors(Y,W),E.subVectors(Z,W),G.cross(E),X.fromBufferAttribute(Q,D),H.fromBufferAttribute(Q,N),K.fromBufferAttribute(Q,O),X.add(G),H.add(G),K.add(G),Q.setXYZ(D,X.x,X.y,X.z),Q.setXYZ(N,H.x,H.y,H.z),Q.setXYZ(O,K.x,K.y,K.z)}else for(let U=0,q=$.count;U<q;U+=3)Z.fromBufferAttribute($,U+0),W.fromBufferAttribute($,U+1),Y.fromBufferAttribute($,U+2),G.subVectors(Y,W),E.subVectors(Z,W),G.cross(E),Q.setXYZ(U+0,G.x,G.y,G.z),Q.setXYZ(U+1,G.x,G.y,G.z),Q.setXYZ(U+2,G.x,G.y,G.z);this.normalizeNormals(),Q.needsUpdate=!0}}normalizeNormals(){let J=this.attributes.normal;for(let $=0,Q=J.count;$<Q;$++)q0.fromBufferAttribute(J,$),q0.normalize(),J.setXYZ($,q0.x,q0.y,q0.z)}toNonIndexed(){function J(X,H){let{array:K,itemSize:G,normalized:E}=X,U=new K.constructor(H.length*G),q=0,D=0;for(let N=0,O=H.length;N<O;N++){if(X.isInterleavedBufferAttribute)q=H[N]*X.data.stride+X.offset;else q=H[N]*G;for(let V=0;V<G;V++)U[D++]=K[q++]}return new I0(U,G,E)}if(this.index===null)return console.warn("THREE.BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;let $=new V0,Q=this.index.array,Z=this.attributes;for(let X in Z){let H=Z[X],K=J(H,Q);$.setAttribute(X,K)}let W=this.morphAttributes;for(let X in W){let H=[],K=W[X];for(let G=0,E=K.length;G<E;G++){let U=K[G],q=J(U,Q);H.push(q)}$.morphAttributes[X]=H}$.morphTargetsRelative=this.morphTargetsRelative;let Y=this.groups;for(let X=0,H=Y.length;X<H;X++){let K=Y[X];$.addGroup(K.start,K.count,K.materialIndex)}return $}toJSON(){let J={metadata:{version:4.6,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(J.uuid=this.uuid,J.type=this.type,this.name!=="")J.name=this.name;if(Object.keys(this.userData).length>0)J.userData=this.userData;if(this.parameters!==void 0){let H=this.parameters;for(let K in H)if(H[K]!==void 0)J[K]=H[K];return J}J.data={attributes:{}};let $=this.index;if($!==null)J.data.index={type:$.array.constructor.name,array:Array.prototype.slice.call($.array)};let Q=this.attributes;for(let H in Q){let K=Q[H];J.data.attributes[H]=K.toJSON(J.data)}let Z={},W=!1;for(let H in this.morphAttributes){let K=this.morphAttributes[H],G=[];for(let E=0,U=K.length;E<U;E++){let q=K[E];G.push(q.toJSON(J.data))}if(G.length>0)Z[H]=G,W=!0}if(W)J.data.morphAttributes=Z,J.data.morphTargetsRelative=this.morphTargetsRelative;let Y=this.groups;if(Y.length>0)J.data.groups=JSON.parse(JSON.stringify(Y));let X=this.boundingSphere;if(X!==null)J.data.boundingSphere={center:X.center.toArray(),radius:X.radius};return J}clone(){return new this.constructor().copy(this)}copy(J){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;let $={};this.name=J.name;let Q=J.index;if(Q!==null)this.setIndex(Q.clone($));let Z=J.attributes;for(let K in Z){let G=Z[K];this.setAttribute(K,G.clone($))}let W=J.morphAttributes;for(let K in W){let G=[],E=W[K];for(let U=0,q=E.length;U<q;U++)G.push(E[U].clone($));this.morphAttributes[K]=G}this.morphTargetsRelative=J.morphTargetsRelative;let Y=J.groups;for(let K=0,G=Y.length;K<G;K++){let E=Y[K];this.addGroup(E.start,E.count,E.materialIndex)}let X=J.boundingBox;if(X!==null)this.boundingBox=X.clone();let H=J.boundingSphere;if(H!==null)this.boundingSphere=H.clone();return this.drawRange.start=J.drawRange.start,this.drawRange.count=J.drawRange.count,this.userData=J.userData,this}dispose(){this.dispatchEvent({type:"dispose"})}}var L9=new Z0,E6=new o7,z7=new l6,_9=new v,k7=new v,A7=new v,w7=new v,k8=new v,L7=new v,C9=new v,_7=new v;class T0 extends R0{constructor(J=new V0,$=new H7){super();this.isMesh=!0,this.type="Mesh",this.geometry=J,this.material=$,this.updateMorphTargets()}copy(J,$){if(super.copy(J,$),J.morphTargetInfluences!==void 0)this.morphTargetInfluences=J.morphTargetInfluences.slice();if(J.morphTargetDictionary!==void 0)this.morphTargetDictionary=Object.assign({},J.morphTargetDictionary);return this.material=Array.isArray(J.material)?J.material.slice():J.material,this.geometry=J.geometry,this}updateMorphTargets(){let $=this.geometry.morphAttributes,Q=Object.keys($);if(Q.length>0){let Z=$[Q[0]];if(Z!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let W=0,Y=Z.length;W<Y;W++){let X=Z[W].name||String(W);this.morphTargetInfluences.push(0),this.morphTargetDictionary[X]=W}}}}getVertexPosition(J,$){let Q=this.geometry,Z=Q.attributes.position,W=Q.morphAttributes.position,Y=Q.morphTargetsRelative;$.fromBufferAttribute(Z,J);let X=this.morphTargetInfluences;if(W&&X){L7.set(0,0,0);for(let H=0,K=W.length;H<K;H++){let G=X[H],E=W[H];if(G===0)continue;if(k8.fromBufferAttribute(E,J),Y)L7.addScaledVector(k8,G);else L7.addScaledVector(k8.sub($),G)}$.add(L7)}return $}raycast(J,$){let Q=this.geometry,Z=this.material,W=this.matrixWorld;if(Z===void 0)return;if(Q.boundingSphere===null)Q.computeBoundingSphere();if(z7.copy(Q.boundingSphere),z7.applyMatrix4(W),E6.copy(J.ray).recast(J.near),z7.containsPoint(E6.origin)===!1){if(E6.intersectSphere(z7,_9)===null)return;if(E6.origin.distanceToSquared(_9)>(J.far-J.near)**2)return}if(L9.copy(W).invert(),E6.copy(J.ray).applyMatrix4(L9),Q.boundingBox!==null){if(E6.intersectsBox(Q.boundingBox)===!1)return}this._computeIntersections(J,$,E6)}_computeIntersections(J,$,Q){let Z,W=this.geometry,Y=this.material,X=W.index,H=W.attributes.position,K=W.attributes.uv,G=W.attributes.uv1,E=W.attributes.normal,U=W.groups,q=W.drawRange;if(X!==null)if(Array.isArray(Y))for(let D=0,N=U.length;D<N;D++){let O=U[D],V=Y[O.materialIndex],F=Math.max(O.start,q.start),A=Math.min(X.count,Math.min(O.start+O.count,q.start+q.count));for(let z=F,_=A;z<_;z+=3){let b=X.getX(z),L=X.getX(z+1),P=X.getX(z+2);if(Z=C7(this,V,J,Q,K,G,E,b,L,P),Z)Z.faceIndex=Math.floor(z/3),Z.face.materialIndex=O.materialIndex,$.push(Z)}}else{let D=Math.max(0,q.start),N=Math.min(X.count,q.start+q.count);for(let O=D,V=N;O<V;O+=3){let F=X.getX(O),A=X.getX(O+1),z=X.getX(O+2);if(Z=C7(this,Y,J,Q,K,G,E,F,A,z),Z)Z.faceIndex=Math.floor(O/3),$.push(Z)}}else if(H!==void 0)if(Array.isArray(Y))for(let D=0,N=U.length;D<N;D++){let O=U[D],V=Y[O.materialIndex],F=Math.max(O.start,q.start),A=Math.min(H.count,Math.min(O.start+O.count,q.start+q.count));for(let z=F,_=A;z<_;z+=3){let b=z,L=z+1,P=z+2;if(Z=C7(this,V,J,Q,K,G,E,b,L,P),Z)Z.faceIndex=Math.floor(z/3),Z.face.materialIndex=O.materialIndex,$.push(Z)}}else{let D=Math.max(0,q.start),N=Math.min(H.count,q.start+q.count);for(let O=D,V=N;O<V;O+=3){let F=O,A=O+1,z=O+2;if(Z=C7(this,Y,J,Q,K,G,E,F,A,z),Z)Z.faceIndex=Math.floor(O/3),$.push(Z)}}}}function E5(J,$,Q,Z,W,Y,X,H){let K;if($.side===1)K=Z.intersectTriangle(X,Y,W,!0,H);else K=Z.intersectTriangle(W,Y,X,$.side===0,H);if(K===null)return null;_7.copy(H),_7.applyMatrix4(J.matrixWorld);let G=Q.ray.origin.distanceTo(_7);if(G<Q.near||G>Q.far)return null;return{distance:G,point:_7.clone(),object:J}}function C7(J,$,Q,Z,W,Y,X,H,K,G){J.getVertexPosition(H,k7),J.getVertexPosition(K,A7),J.getVertexPosition(G,w7);let E=E5(J,$,Q,Z,k7,A7,w7,C9);if(E){let U=new v;if(_0.getBarycoord(C9,k7,A7,w7,U),W)E.uv=_0.getInterpolatedAttribute(W,H,K,G,U,new uJ);if(Y)E.uv1=_0.getInterpolatedAttribute(Y,H,K,G,U,new uJ);if(X){if(E.normal=_0.getInterpolatedAttribute(X,H,K,G,U,new v),E.normal.dot(Z.direction)>0)E.normal.multiplyScalar(-1)}let q={a:H,b:K,c:G,normal:new v,materialIndex:0};_0.getNormal(k7,A7,w7,q.normal),E.face=q,E.barycoord=U}return E}class X0 extends V0{constructor(J=1,$=1,Q=1,Z=1,W=1,Y=1){super();this.type="BoxGeometry",this.parameters={width:J,height:$,depth:Q,widthSegments:Z,heightSegments:W,depthSegments:Y};let X=this;Z=Math.floor(Z),W=Math.floor(W),Y=Math.floor(Y);let H=[],K=[],G=[],E=[],U=0,q=0;D("z","y","x",-1,-1,Q,$,J,Y,W,0),D("z","y","x",1,-1,Q,$,-J,Y,W,1),D("x","z","y",1,1,J,Q,$,Z,Y,2),D("x","z","y",1,-1,J,Q,-$,Z,Y,3),D("x","y","z",1,-1,J,$,Q,Z,W,4),D("x","y","z",-1,-1,J,$,-Q,Z,W,5),this.setIndex(H),this.setAttribute("position",new Y0(K,3)),this.setAttribute("normal",new Y0(G,3)),this.setAttribute("uv",new Y0(E,2));function D(N,O,V,F,A,z,_,b,L,P,p){let B=z/L,k=_/P,T=z/2,x=_/2,m=b/2,u=L+1,a=P+1,l=0,t=0,g=new v;for(let XJ=0;XJ<a;XJ++){let ZJ=XJ*k-x;for(let _J=0;_J<u;_J++){let fJ=_J*B-T;g[N]=fJ*F,g[O]=ZJ*A,g[V]=m,K.push(g.x,g.y,g.z),g[N]=0,g[O]=0,g[V]=b>0?1:-1,G.push(g.x,g.y,g.z),E.push(_J/L),E.push(1-XJ/P),l+=1}}for(let XJ=0;XJ<P;XJ++)for(let ZJ=0;ZJ<L;ZJ++){let _J=U+ZJ+u*XJ,fJ=U+ZJ+u*(XJ+1),n=U+(ZJ+1)+u*(XJ+1),e=U+(ZJ+1)+u*XJ;H.push(_J,fJ,e),H.push(fJ,n,e),t+=6}X.addGroup(q,t,p),q+=t,U+=l}}copy(J){return super.copy(J),this.parameters=Object.assign({},J.parameters),this}static fromJSON(J){return new X0(J.width,J.height,J.depth,J.widthSegments,J.heightSegments,J.depthSegments)}}function m6(J){let $={};for(let Q in J){$[Q]={};for(let Z in J[Q]){let W=J[Q][Z];if(W&&(W.isColor||W.isMatrix3||W.isMatrix4||W.isVector2||W.isVector3||W.isVector4||W.isTexture||W.isQuaternion))if(W.isRenderTargetTexture)console.warn("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),$[Q][Z]=null;else $[Q][Z]=W.clone();else if(Array.isArray(W))$[Q][Z]=W.slice();else $[Q][Z]=W}}return $}function O0(J){let $={};for(let Q=0;Q<J.length;Q++){let Z=m6(J[Q]);for(let W in Z)$[W]=Z[W]}return $}function V5(J){let $=[];for(let Q=0;Q<J.length;Q++)$.push(J[Q].clone());return $}function F$(J){let $=J.getRenderTarget();if($===null)return J.outputColorSpace;if($.isXRRenderTarget===!0)return $.texture.colorSpace;return dJ.workingColorSpace}var F5={clone:m6,merge:O0},D5=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,R5=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`;class a0 extends K6{static get type(){return"ShaderMaterial"}constructor(J){super();if(this.isShaderMaterial=!0,this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=D5,this.fragmentShader=R5,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,J!==void 0)this.setValues(J)}copy(J){return super.copy(J),this.fragmentShader=J.fragmentShader,this.vertexShader=J.vertexShader,this.uniforms=m6(J.uniforms),this.uniformsGroups=V5(J.uniformsGroups),this.defines=Object.assign({},J.defines),this.wireframe=J.wireframe,this.wireframeLinewidth=J.wireframeLinewidth,this.fog=J.fog,this.lights=J.lights,this.clipping=J.clipping,this.extensions=Object.assign({},J.extensions),this.glslVersion=J.glslVersion,this}toJSON(J){let $=super.toJSON(J);$.glslVersion=this.glslVersion,$.uniforms={};for(let Z in this.uniforms){let Y=this.uniforms[Z].value;if(Y&&Y.isTexture)$.uniforms[Z]={type:"t",value:Y.toJSON(J).uuid};else if(Y&&Y.isColor)$.uniforms[Z]={type:"c",value:Y.getHex()};else if(Y&&Y.isVector2)$.uniforms[Z]={type:"v2",value:Y.toArray()};else if(Y&&Y.isVector3)$.uniforms[Z]={type:"v3",value:Y.toArray()};else if(Y&&Y.isVector4)$.uniforms[Z]={type:"v4",value:Y.toArray()};else if(Y&&Y.isMatrix3)$.uniforms[Z]={type:"m3",value:Y.toArray()};else if(Y&&Y.isMatrix4)$.uniforms[Z]={type:"m4",value:Y.toArray()};else $.uniforms[Z]={value:Y}}if(Object.keys(this.defines).length>0)$.defines=this.defines;$.vertexShader=this.vertexShader,$.fragmentShader=this.fragmentShader,$.lights=this.lights,$.clipping=this.clipping;let Q={};for(let Z in this.extensions)if(this.extensions[Z]===!0)Q[Z]=!0;if(Object.keys(Q).length>0)$.extensions=Q;return $}}class u8 extends R0{constructor(){super();this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new Z0,this.projectionMatrix=new Z0,this.projectionMatrixInverse=new Z0,this.coordinateSystem=2000}copy(J,$){return super.copy(J,$),this.matrixWorldInverse.copy(J.matrixWorldInverse),this.projectionMatrix.copy(J.projectionMatrix),this.projectionMatrixInverse.copy(J.projectionMatrixInverse),this.coordinateSystem=J.coordinateSystem,this}getWorldDirection(J){return super.getWorldDirection(J).negate()}updateMatrixWorld(J){super.updateMatrixWorld(J),this.matrixWorldInverse.copy(this.matrixWorld).invert()}updateWorldMatrix(J,$){super.updateWorldMatrix(J,$),this.matrixWorldInverse.copy(this.matrixWorld).invert()}clone(){return new this.constructor().copy(this)}}var W6=new v,P9=new uJ,T9=new uJ;class k0 extends u8{constructor(J=50,$=1,Q=0.1,Z=2000){super();this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=J,this.zoom=1,this.near=Q,this.far=Z,this.focus=10,this.aspect=$,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(J,$){return super.copy(J,$),this.fov=J.fov,this.zoom=J.zoom,this.near=J.near,this.far=J.far,this.focus=J.focus,this.aspect=J.aspect,this.view=J.view===null?null:Object.assign({},J.view),this.filmGauge=J.filmGauge,this.filmOffset=J.filmOffset,this}setFocalLength(J){let $=0.5*this.getFilmHeight()/J;this.fov=v8*2*Math.atan($),this.updateProjectionMatrix()}getFocalLength(){let J=Math.tan(l7*0.5*this.fov);return 0.5*this.getFilmHeight()/J}getEffectiveFOV(){return v8*2*Math.atan(Math.tan(l7*0.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(J,$,Q){W6.set(-1,-1,0.5).applyMatrix4(this.projectionMatrixInverse),$.set(W6.x,W6.y).multiplyScalar(-J/W6.z),W6.set(1,1,0.5).applyMatrix4(this.projectionMatrixInverse),Q.set(W6.x,W6.y).multiplyScalar(-J/W6.z)}getViewSize(J,$){return this.getViewBounds(J,P9,T9),$.subVectors(T9,P9)}setViewOffset(J,$,Q,Z,W,Y){if(this.aspect=J/$,this.view===null)this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1};this.view.enabled=!0,this.view.fullWidth=J,this.view.fullHeight=$,this.view.offsetX=Q,this.view.offsetY=Z,this.view.width=W,this.view.height=Y,this.updateProjectionMatrix()}clearViewOffset(){if(this.view!==null)this.view.enabled=!1;this.updateProjectionMatrix()}updateProjectionMatrix(){let J=this.near,$=J*Math.tan(l7*0.5*this.fov)/this.zoom,Q=2*$,Z=this.aspect*Q,W=-0.5*Z,Y=this.view;if(this.view!==null&&this.view.enabled){let{fullWidth:H,fullHeight:K}=Y;W+=Y.offsetX*Z/H,$-=Y.offsetY*Q/K,Z*=Y.width/H,Q*=Y.height/K}let X=this.filmOffset;if(X!==0)W+=J*X/this.getFilmWidth();this.projectionMatrix.makePerspective(W,W+Z,$,$-Q,J,this.far,this.coordinateSystem),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(J){let $=super.toJSON(J);if($.object.fov=this.fov,$.object.zoom=this.zoom,$.object.near=this.near,$.object.far=this.far,$.object.focus=this.focus,$.object.aspect=this.aspect,this.view!==null)$.object.view=Object.assign({},this.view);return $.object.filmGauge=this.filmGauge,$.object.filmOffset=this.filmOffset,$}}var y6=-90,v6=1;class D$ extends R0{constructor(J,$,Q){super();this.type="CubeCamera",this.renderTarget=Q,this.coordinateSystem=null,this.activeMipmapLevel=0;let Z=new k0(y6,v6,J,$);Z.layers=this.layers,this.add(Z);let W=new k0(y6,v6,J,$);W.layers=this.layers,this.add(W);let Y=new k0(y6,v6,J,$);Y.layers=this.layers,this.add(Y);let X=new k0(y6,v6,J,$);X.layers=this.layers,this.add(X);let H=new k0(y6,v6,J,$);H.layers=this.layers,this.add(H);let K=new k0(y6,v6,J,$);K.layers=this.layers,this.add(K)}updateCoordinateSystem(){let J=this.coordinateSystem,$=this.children.concat(),[Q,Z,W,Y,X,H]=$;for(let K of $)this.remove(K);if(J===2000)Q.up.set(0,1,0),Q.lookAt(1,0,0),Z.up.set(0,1,0),Z.lookAt(-1,0,0),W.up.set(0,0,-1),W.lookAt(0,1,0),Y.up.set(0,0,1),Y.lookAt(0,-1,0),X.up.set(0,1,0),X.lookAt(0,0,1),H.up.set(0,1,0),H.lookAt(0,0,-1);else if(J===2001)Q.up.set(0,-1,0),Q.lookAt(-1,0,0),Z.up.set(0,-1,0),Z.lookAt(1,0,0),W.up.set(0,0,1),W.lookAt(0,1,0),Y.up.set(0,0,-1),Y.lookAt(0,-1,0),X.up.set(0,-1,0),X.lookAt(0,0,1),H.up.set(0,-1,0),H.lookAt(0,0,-1);else throw Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+J);for(let K of $)this.add(K),K.updateMatrixWorld()}update(J,$){if(this.parent===null)this.updateMatrixWorld();let{renderTarget:Q,activeMipmapLevel:Z}=this;if(this.coordinateSystem!==J.coordinateSystem)this.coordinateSystem=J.coordinateSystem,this.updateCoordinateSystem();let[W,Y,X,H,K,G]=this.children,E=J.getRenderTarget(),U=J.getActiveCubeFace(),q=J.getActiveMipmapLevel(),D=J.xr.enabled;J.xr.enabled=!1;let N=Q.texture.generateMipmaps;Q.texture.generateMipmaps=!1,J.setRenderTarget(Q,0,Z),J.render($,W),J.setRenderTarget(Q,1,Z),J.render($,Y),J.setRenderTarget(Q,2,Z),J.render($,X),J.setRenderTarget(Q,3,Z),J.render($,H),J.setRenderTarget(Q,4,Z),J.render($,K),Q.texture.generateMipmaps=N,J.setRenderTarget(Q,5,Z),J.render($,G),J.setRenderTarget(E,U,q),J.xr.enabled=D,Q.texture.needsPMREMUpdate=!0}}class l8 extends M0{constructor(J,$,Q,Z,W,Y,X,H,K,G){J=J!==void 0?J:[],$=$!==void 0?$:301;super(J,$,Q,Z,W,Y,X,H,K,G);this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(J){this.image=J}}class R$ extends X6{constructor(J=1,$={}){super(J,J,$);this.isWebGLCubeRenderTarget=!0;let Q={width:J,height:J,depth:1},Z=[Q,Q,Q,Q,Q,Q];this.texture=new l8(Z,$.mapping,$.wrapS,$.wrapT,$.magFilter,$.minFilter,$.format,$.type,$.anisotropy,$.colorSpace),this.texture.isRenderTargetTexture=!0,this.texture.generateMipmaps=$.generateMipmaps!==void 0?$.generateMipmaps:!1,this.texture.minFilter=$.minFilter!==void 0?$.minFilter:1006}fromEquirectangularTexture(J,$){this.texture.type=$.type,this.texture.colorSpace=$.colorSpace,this.texture.generateMipmaps=$.generateMipmaps,this.texture.minFilter=$.minFilter,this.texture.magFilter=$.magFilter;let Q={uniforms:{tEquirect:{value:null}},vertexShader:`

				varying vec3 vWorldDirection;

				vec3 transformDirection( in vec3 dir, in mat4 matrix ) {

					return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );

				}

				void main() {

					vWorldDirection = transformDirection( position, modelMatrix );

					#include <begin_vertex>
					#include <project_vertex>

				}
			`,fragmentShader:`

				uniform sampler2D tEquirect;

				varying vec3 vWorldDirection;

				#include <common>

				void main() {

					vec3 direction = normalize( vWorldDirection );

					vec2 sampleUV = equirectUv( direction );

					gl_FragColor = texture2D( tEquirect, sampleUV );

				}
			`},Z=new X0(5,5,5),W=new a0({name:"CubemapFromEquirect",uniforms:m6(Q.uniforms),vertexShader:Q.vertexShader,fragmentShader:Q.fragmentShader,side:1,blending:0});W.uniforms.tEquirect.value=$;let Y=new T0(Z,W),X=$.minFilter;if($.minFilter===1008)$.minFilter=1006;return new D$(1,10,this).update(J,Y),$.minFilter=X,Y.geometry.dispose(),Y.material.dispose(),this}clear(J,$,Q,Z){let W=J.getRenderTarget();for(let Y=0;Y<6;Y++)J.setRenderTarget(this,Y),J.clear($,Q,Z);J.setRenderTarget(W)}}var A8=new v,N5=new v,O5=new jJ;class Y6{constructor(J=new v(1,0,0),$=0){this.isPlane=!0,this.normal=J,this.constant=$}set(J,$){return this.normal.copy(J),this.constant=$,this}setComponents(J,$,Q,Z){return this.normal.set(J,$,Q),this.constant=Z,this}setFromNormalAndCoplanarPoint(J,$){return this.normal.copy(J),this.constant=-$.dot(this.normal),this}setFromCoplanarPoints(J,$,Q){let Z=A8.subVectors(Q,$).cross(N5.subVectors(J,$)).normalize();return this.setFromNormalAndCoplanarPoint(Z,J),this}copy(J){return this.normal.copy(J.normal),this.constant=J.constant,this}normalize(){let J=1/this.normal.length();return this.normal.multiplyScalar(J),this.constant*=J,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(J){return this.normal.dot(J)+this.constant}distanceToSphere(J){return this.distanceToPoint(J.center)-J.radius}projectPoint(J,$){return $.copy(J).addScaledVector(this.normal,-this.distanceToPoint(J))}intersectLine(J,$){let Q=J.delta(A8),Z=this.normal.dot(Q);if(Z===0){if(this.distanceToPoint(J.start)===0)return $.copy(J.start);return null}let W=-(J.start.dot(this.normal)+this.constant)/Z;if(W<0||W>1)return null;return $.copy(J.start).addScaledVector(Q,W)}intersectsLine(J){let $=this.distanceToPoint(J.start),Q=this.distanceToPoint(J.end);return $<0&&Q>0||Q<0&&$>0}intersectsBox(J){return J.intersectsPlane(this)}intersectsSphere(J){return J.intersectsPlane(this)}coplanarPoint(J){return J.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(J,$){let Q=$||O5.getNormalMatrix(J),Z=this.coplanarPoint(A8).applyMatrix4(J),W=this.normal.applyMatrix3(Q).normalize();return this.constant=-Z.dot(W),this}translate(J){return this.constant-=J.dot(this.normal),this}equals(J){return J.normal.equals(this.normal)&&J.constant===this.constant}clone(){return new this.constructor().copy(this)}}var V6=new l6,P7=new v;class d8{constructor(J=new Y6,$=new Y6,Q=new Y6,Z=new Y6,W=new Y6,Y=new Y6){this.planes=[J,$,Q,Z,W,Y]}set(J,$,Q,Z,W,Y){let X=this.planes;return X[0].copy(J),X[1].copy($),X[2].copy(Q),X[3].copy(Z),X[4].copy(W),X[5].copy(Y),this}copy(J){let $=this.planes;for(let Q=0;Q<6;Q++)$[Q].copy(J.planes[Q]);return this}setFromProjectionMatrix(J,$=2000){let Q=this.planes,Z=J.elements,W=Z[0],Y=Z[1],X=Z[2],H=Z[3],K=Z[4],G=Z[5],E=Z[6],U=Z[7],q=Z[8],D=Z[9],N=Z[10],O=Z[11],V=Z[12],F=Z[13],A=Z[14],z=Z[15];if(Q[0].setComponents(H-W,U-K,O-q,z-V).normalize(),Q[1].setComponents(H+W,U+K,O+q,z+V).normalize(),Q[2].setComponents(H+Y,U+G,O+D,z+F).normalize(),Q[3].setComponents(H-Y,U-G,O-D,z-F).normalize(),Q[4].setComponents(H-X,U-E,O-N,z-A).normalize(),$===2000)Q[5].setComponents(H+X,U+E,O+N,z+A).normalize();else if($===2001)Q[5].setComponents(X,E,N,A).normalize();else throw Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+$);return this}intersectsObject(J){if(J.boundingSphere!==void 0){if(J.boundingSphere===null)J.computeBoundingSphere();V6.copy(J.boundingSphere).applyMatrix4(J.matrixWorld)}else{let $=J.geometry;if($.boundingSphere===null)$.computeBoundingSphere();V6.copy($.boundingSphere).applyMatrix4(J.matrixWorld)}return this.intersectsSphere(V6)}intersectsSprite(J){return V6.center.set(0,0,0),V6.radius=0.7071067811865476,V6.applyMatrix4(J.matrixWorld),this.intersectsSphere(V6)}intersectsSphere(J){let $=this.planes,Q=J.center,Z=-J.radius;for(let W=0;W<6;W++)if($[W].distanceToPoint(Q)<Z)return!1;return!0}intersectsBox(J){let $=this.planes;for(let Q=0;Q<6;Q++){let Z=$[Q];if(P7.x=Z.normal.x>0?J.max.x:J.min.x,P7.y=Z.normal.y>0?J.max.y:J.min.y,P7.z=Z.normal.z>0?J.max.z:J.min.z,Z.distanceToPoint(P7)<0)return!1}return!0}containsPoint(J){let $=this.planes;for(let Q=0;Q<6;Q++)if($[Q].distanceToPoint(J)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}}function N$(){let J=null,$=!1,Q=null,Z=null;function W(Y,X){Q(Y,X),Z=J.requestAnimationFrame(W)}return{start:function(){if($===!0)return;if(Q===null)return;Z=J.requestAnimationFrame(W),$=!0},stop:function(){J.cancelAnimationFrame(Z),$=!1},setAnimationLoop:function(Y){Q=Y},setContext:function(Y){J=Y}}}function M5(J){let $=new WeakMap;function Q(H,K){let{array:G,usage:E}=H,U=G.byteLength,q=J.createBuffer();J.bindBuffer(K,q),J.bufferData(K,G,E),H.onUploadCallback();let D;if(G instanceof Float32Array)D=J.FLOAT;else if(G instanceof Uint16Array)if(H.isFloat16BufferAttribute)D=J.HALF_FLOAT;else D=J.UNSIGNED_SHORT;else if(G instanceof Int16Array)D=J.SHORT;else if(G instanceof Uint32Array)D=J.UNSIGNED_INT;else if(G instanceof Int32Array)D=J.INT;else if(G instanceof Int8Array)D=J.BYTE;else if(G instanceof Uint8Array)D=J.UNSIGNED_BYTE;else if(G instanceof Uint8ClampedArray)D=J.UNSIGNED_BYTE;else throw Error("THREE.WebGLAttributes: Unsupported buffer data format: "+G);return{buffer:q,type:D,bytesPerElement:G.BYTES_PER_ELEMENT,version:H.version,size:U}}function Z(H,K,G){let{array:E,updateRanges:U}=K;if(J.bindBuffer(G,H),U.length===0)J.bufferSubData(G,0,E);else{U.sort((D,N)=>D.start-N.start);let q=0;for(let D=1;D<U.length;D++){let N=U[q],O=U[D];if(O.start<=N.start+N.count+1)N.count=Math.max(N.count,O.start+O.count-N.start);else++q,U[q]=O}U.length=q+1;for(let D=0,N=U.length;D<N;D++){let O=U[D];J.bufferSubData(G,O.start*E.BYTES_PER_ELEMENT,E,O.start,O.count)}K.clearUpdateRanges()}K.onUploadCallback()}function W(H){if(H.isInterleavedBufferAttribute)H=H.data;return $.get(H)}function Y(H){if(H.isInterleavedBufferAttribute)H=H.data;let K=$.get(H);if(K)J.deleteBuffer(K.buffer),$.delete(H)}function X(H,K){if(H.isInterleavedBufferAttribute)H=H.data;if(H.isGLBufferAttribute){let E=$.get(H);if(!E||E.version<H.version)$.set(H,{buffer:H.buffer,type:H.type,bytesPerElement:H.elementSize,version:H.version});return}let G=$.get(H);if(G===void 0)$.set(H,Q(H,K));else if(G.version<H.version){if(G.size!==H.array.byteLength)throw Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");Z(G.buffer,H,K),G.version=H.version}}return{get:W,remove:Y,update:X}}class a7 extends V0{constructor(J=1,$=1,Q=1,Z=1){super();this.type="PlaneGeometry",this.parameters={width:J,height:$,widthSegments:Q,heightSegments:Z};let W=J/2,Y=$/2,X=Math.floor(Q),H=Math.floor(Z),K=X+1,G=H+1,E=J/X,U=$/H,q=[],D=[],N=[],O=[];for(let V=0;V<G;V++){let F=V*U-Y;for(let A=0;A<K;A++){let z=A*E-W;D.push(z,-F,0),N.push(0,0,1),O.push(A/X),O.push(1-V/H)}}for(let V=0;V<H;V++)for(let F=0;F<X;F++){let A=F+K*V,z=F+K*(V+1),_=F+1+K*(V+1),b=F+1+K*V;q.push(A,z,b),q.push(z,_,b)}this.setIndex(q),this.setAttribute("position",new Y0(D,3)),this.setAttribute("normal",new Y0(N,3)),this.setAttribute("uv",new Y0(O,2))}copy(J){return super.copy(J),this.parameters=Object.assign({},J.parameters),this}static fromJSON(J){return new a7(J.width,J.height,J.widthSegments,J.heightSegments)}}var B5=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,z5=`#ifdef USE_ALPHAHASH
	const float ALPHA_HASH_SCALE = 0.05;
	float hash2D( vec2 value ) {
		return fract( 1.0e4 * sin( 17.0 * value.x + 0.1 * value.y ) * ( 0.1 + abs( sin( 13.0 * value.y + value.x ) ) ) );
	}
	float hash3D( vec3 value ) {
		return hash2D( vec2( hash2D( value.xy ), value.z ) );
	}
	float getAlphaHashThreshold( vec3 position ) {
		float maxDeriv = max(
			length( dFdx( position.xyz ) ),
			length( dFdy( position.xyz ) )
		);
		float pixScale = 1.0 / ( ALPHA_HASH_SCALE * maxDeriv );
		vec2 pixScales = vec2(
			exp2( floor( log2( pixScale ) ) ),
			exp2( ceil( log2( pixScale ) ) )
		);
		vec2 alpha = vec2(
			hash3D( floor( pixScales.x * position.xyz ) ),
			hash3D( floor( pixScales.y * position.xyz ) )
		);
		float lerpFactor = fract( log2( pixScale ) );
		float x = ( 1.0 - lerpFactor ) * alpha.x + lerpFactor * alpha.y;
		float a = min( lerpFactor, 1.0 - lerpFactor );
		vec3 cases = vec3(
			x * x / ( 2.0 * a * ( 1.0 - a ) ),
			( x - 0.5 * a ) / ( 1.0 - a ),
			1.0 - ( ( 1.0 - x ) * ( 1.0 - x ) / ( 2.0 * a * ( 1.0 - a ) ) )
		);
		float threshold = ( x < ( 1.0 - a ) )
			? ( ( x < a ) ? cases.x : cases.y )
			: cases.z;
		return clamp( threshold , 1.0e-6, 1.0 );
	}
#endif`,k5=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,A5=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,w5=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,L5=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,_5=`#ifdef USE_AOMAP
	float ambientOcclusion = ( texture2D( aoMap, vAoMapUv ).r - 1.0 ) * aoMapIntensity + 1.0;
	reflectedLight.indirectDiffuse *= ambientOcclusion;
	#if defined( USE_CLEARCOAT ) 
		clearcoatSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_SHEEN ) 
		sheenSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD )
		float dotNV = saturate( dot( geometryNormal, geometryViewDir ) );
		reflectedLight.indirectSpecular *= computeSpecularOcclusion( dotNV, ambientOcclusion, material.roughness );
	#endif
#endif`,C5=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,P5=`#ifdef USE_BATCHING
	#if ! defined( GL_ANGLE_multi_draw )
	#define gl_DrawID _gl_DrawID
	uniform int _gl_DrawID;
	#endif
	uniform highp sampler2D batchingTexture;
	uniform highp usampler2D batchingIdTexture;
	mat4 getBatchingMatrix( const in float i ) {
		int size = textureSize( batchingTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( batchingTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( batchingTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( batchingTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( batchingTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
	float getIndirectIndex( const in int i ) {
		int size = textureSize( batchingIdTexture, 0 ).x;
		int x = i % size;
		int y = i / size;
		return float( texelFetch( batchingIdTexture, ivec2( x, y ), 0 ).r );
	}
#endif
#ifdef USE_BATCHING_COLOR
	uniform sampler2D batchingColorTexture;
	vec3 getBatchingColor( const in float i ) {
		int size = textureSize( batchingColorTexture, 0 ).x;
		int j = int( i );
		int x = j % size;
		int y = j / size;
		return texelFetch( batchingColorTexture, ivec2( x, y ), 0 ).rgb;
	}
#endif`,T5=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,I5=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,S5=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,y5=`float G_BlinnPhong_Implicit( ) {
	return 0.25;
}
float D_BlinnPhong( const in float shininess, const in float dotNH ) {
	return RECIPROCAL_PI * ( shininess * 0.5 + 1.0 ) * pow( dotNH, shininess );
}
vec3 BRDF_BlinnPhong( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in vec3 specularColor, const in float shininess ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( specularColor, 1.0, dotVH );
	float G = G_BlinnPhong_Implicit( );
	float D = D_BlinnPhong( shininess, dotNH );
	return F * ( G * D );
} // validated`,v5=`#ifdef USE_IRIDESCENCE
	const mat3 XYZ_TO_REC709 = mat3(
		 3.2404542, -0.9692660,  0.0556434,
		-1.5371385,  1.8760108, -0.2040259,
		-0.4985314,  0.0415560,  1.0572252
	);
	vec3 Fresnel0ToIor( vec3 fresnel0 ) {
		vec3 sqrtF0 = sqrt( fresnel0 );
		return ( vec3( 1.0 ) + sqrtF0 ) / ( vec3( 1.0 ) - sqrtF0 );
	}
	vec3 IorToFresnel0( vec3 transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - vec3( incidentIor ) ) / ( transmittedIor + vec3( incidentIor ) ) );
	}
	float IorToFresnel0( float transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - incidentIor ) / ( transmittedIor + incidentIor ));
	}
	vec3 evalSensitivity( float OPD, vec3 shift ) {
		float phase = 2.0 * PI * OPD * 1.0e-9;
		vec3 val = vec3( 5.4856e-13, 4.4201e-13, 5.2481e-13 );
		vec3 pos = vec3( 1.6810e+06, 1.7953e+06, 2.2084e+06 );
		vec3 var = vec3( 4.3278e+09, 9.3046e+09, 6.6121e+09 );
		vec3 xyz = val * sqrt( 2.0 * PI * var ) * cos( pos * phase + shift ) * exp( - pow2( phase ) * var );
		xyz.x += 9.7470e-14 * sqrt( 2.0 * PI * 4.5282e+09 ) * cos( 2.2399e+06 * phase + shift[ 0 ] ) * exp( - 4.5282e+09 * pow2( phase ) );
		xyz /= 1.0685e-7;
		vec3 rgb = XYZ_TO_REC709 * xyz;
		return rgb;
	}
	vec3 evalIridescence( float outsideIOR, float eta2, float cosTheta1, float thinFilmThickness, vec3 baseF0 ) {
		vec3 I;
		float iridescenceIOR = mix( outsideIOR, eta2, smoothstep( 0.0, 0.03, thinFilmThickness ) );
		float sinTheta2Sq = pow2( outsideIOR / iridescenceIOR ) * ( 1.0 - pow2( cosTheta1 ) );
		float cosTheta2Sq = 1.0 - sinTheta2Sq;
		if ( cosTheta2Sq < 0.0 ) {
			return vec3( 1.0 );
		}
		float cosTheta2 = sqrt( cosTheta2Sq );
		float R0 = IorToFresnel0( iridescenceIOR, outsideIOR );
		float R12 = F_Schlick( R0, 1.0, cosTheta1 );
		float T121 = 1.0 - R12;
		float phi12 = 0.0;
		if ( iridescenceIOR < outsideIOR ) phi12 = PI;
		float phi21 = PI - phi12;
		vec3 baseIOR = Fresnel0ToIor( clamp( baseF0, 0.0, 0.9999 ) );		vec3 R1 = IorToFresnel0( baseIOR, iridescenceIOR );
		vec3 R23 = F_Schlick( R1, 1.0, cosTheta2 );
		vec3 phi23 = vec3( 0.0 );
		if ( baseIOR[ 0 ] < iridescenceIOR ) phi23[ 0 ] = PI;
		if ( baseIOR[ 1 ] < iridescenceIOR ) phi23[ 1 ] = PI;
		if ( baseIOR[ 2 ] < iridescenceIOR ) phi23[ 2 ] = PI;
		float OPD = 2.0 * iridescenceIOR * thinFilmThickness * cosTheta2;
		vec3 phi = vec3( phi21 ) + phi23;
		vec3 R123 = clamp( R12 * R23, 1e-5, 0.9999 );
		vec3 r123 = sqrt( R123 );
		vec3 Rs = pow2( T121 ) * R23 / ( vec3( 1.0 ) - R123 );
		vec3 C0 = R12 + Rs;
		I = C0;
		vec3 Cm = Rs - T121;
		for ( int m = 1; m <= 2; ++ m ) {
			Cm *= r123;
			vec3 Sm = 2.0 * evalSensitivity( float( m ) * OPD, float( m ) * phi );
			I += Cm * Sm;
		}
		return max( I, vec3( 0.0 ) );
	}
#endif`,j5=`#ifdef USE_BUMPMAP
	uniform sampler2D bumpMap;
	uniform float bumpScale;
	vec2 dHdxy_fwd() {
		vec2 dSTdx = dFdx( vBumpMapUv );
		vec2 dSTdy = dFdy( vBumpMapUv );
		float Hll = bumpScale * texture2D( bumpMap, vBumpMapUv ).x;
		float dBx = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdx ).x - Hll;
		float dBy = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdy ).x - Hll;
		return vec2( dBx, dBy );
	}
	vec3 perturbNormalArb( vec3 surf_pos, vec3 surf_norm, vec2 dHdxy, float faceDirection ) {
		vec3 vSigmaX = normalize( dFdx( surf_pos.xyz ) );
		vec3 vSigmaY = normalize( dFdy( surf_pos.xyz ) );
		vec3 vN = surf_norm;
		vec3 R1 = cross( vSigmaY, vN );
		vec3 R2 = cross( vN, vSigmaX );
		float fDet = dot( vSigmaX, R1 ) * faceDirection;
		vec3 vGrad = sign( fDet ) * ( dHdxy.x * R1 + dHdxy.y * R2 );
		return normalize( abs( fDet ) * surf_norm - vGrad );
	}
#endif`,f5=`#if NUM_CLIPPING_PLANES > 0
	vec4 plane;
	#ifdef ALPHA_TO_COVERAGE
		float distanceToPlane, distanceGradient;
		float clipOpacity = 1.0;
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
			distanceGradient = fwidth( distanceToPlane ) / 2.0;
			clipOpacity *= smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			if ( clipOpacity == 0.0 ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			float unionClipOpacity = 1.0;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
				distanceGradient = fwidth( distanceToPlane ) / 2.0;
				unionClipOpacity *= 1.0 - smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			}
			#pragma unroll_loop_end
			clipOpacity *= 1.0 - unionClipOpacity;
		#endif
		diffuseColor.a *= clipOpacity;
		if ( diffuseColor.a == 0.0 ) discard;
	#else
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			if ( dot( vClipPosition, plane.xyz ) > plane.w ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			bool clipped = true;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				clipped = ( dot( vClipPosition, plane.xyz ) > plane.w ) && clipped;
			}
			#pragma unroll_loop_end
			if ( clipped ) discard;
		#endif
	#endif
#endif`,h5=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,b5=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,x5=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,p5=`#if defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#elif defined( USE_COLOR )
	diffuseColor.rgb *= vColor;
#endif`,g5=`#if defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#elif defined( USE_COLOR )
	varying vec3 vColor;
#endif`,m5=`#if defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#elif defined( USE_COLOR ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec3 vColor;
#endif`,u5=`#if defined( USE_COLOR_ALPHA )
	vColor = vec4( 1.0 );
#elif defined( USE_COLOR ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	vColor = vec3( 1.0 );
#endif
#ifdef USE_COLOR
	vColor *= color;
#endif
#ifdef USE_INSTANCING_COLOR
	vColor.xyz *= instanceColor.xyz;
#endif
#ifdef USE_BATCHING_COLOR
	vec3 batchingColor = getBatchingColor( getIndirectIndex( gl_DrawID ) );
	vColor.xyz *= batchingColor.xyz;
#endif`,l5=`#define PI 3.141592653589793
#define PI2 6.283185307179586
#define PI_HALF 1.5707963267948966
#define RECIPROCAL_PI 0.3183098861837907
#define RECIPROCAL_PI2 0.15915494309189535
#define EPSILON 1e-6
#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
#define whiteComplement( a ) ( 1.0 - saturate( a ) )
float pow2( const in float x ) { return x*x; }
vec3 pow2( const in vec3 x ) { return x*x; }
float pow3( const in float x ) { return x*x*x; }
float pow4( const in float x ) { float x2 = x*x; return x2*x2; }
float max3( const in vec3 v ) { return max( max( v.x, v.y ), v.z ); }
float average( const in vec3 v ) { return dot( v, vec3( 0.3333333 ) ); }
highp float rand( const in vec2 uv ) {
	const highp float a = 12.9898, b = 78.233, c = 43758.5453;
	highp float dt = dot( uv.xy, vec2( a,b ) ), sn = mod( dt, PI );
	return fract( sin( sn ) * c );
}
#ifdef HIGH_PRECISION
	float precisionSafeLength( vec3 v ) { return length( v ); }
#else
	float precisionSafeLength( vec3 v ) {
		float maxComponent = max3( abs( v ) );
		return length( v / maxComponent ) * maxComponent;
	}
#endif
struct IncidentLight {
	vec3 color;
	vec3 direction;
	bool visible;
};
struct ReflectedLight {
	vec3 directDiffuse;
	vec3 directSpecular;
	vec3 indirectDiffuse;
	vec3 indirectSpecular;
};
#ifdef USE_ALPHAHASH
	varying vec3 vPosition;
#endif
vec3 transformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );
}
vec3 inverseTransformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( vec4( dir, 0.0 ) * matrix ).xyz );
}
mat3 transposeMat3( const in mat3 m ) {
	mat3 tmp;
	tmp[ 0 ] = vec3( m[ 0 ].x, m[ 1 ].x, m[ 2 ].x );
	tmp[ 1 ] = vec3( m[ 0 ].y, m[ 1 ].y, m[ 2 ].y );
	tmp[ 2 ] = vec3( m[ 0 ].z, m[ 1 ].z, m[ 2 ].z );
	return tmp;
}
bool isPerspectiveMatrix( mat4 m ) {
	return m[ 2 ][ 3 ] == - 1.0;
}
vec2 equirectUv( in vec3 dir ) {
	float u = atan( dir.z, dir.x ) * RECIPROCAL_PI2 + 0.5;
	float v = asin( clamp( dir.y, - 1.0, 1.0 ) ) * RECIPROCAL_PI + 0.5;
	return vec2( u, v );
}
vec3 BRDF_Lambert( const in vec3 diffuseColor ) {
	return RECIPROCAL_PI * diffuseColor;
}
vec3 F_Schlick( const in vec3 f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
}
float F_Schlick( const in float f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
} // validated`,d5=`#ifdef ENVMAP_TYPE_CUBE_UV
	#define cubeUV_minMipLevel 4.0
	#define cubeUV_minTileSize 16.0
	float getFace( vec3 direction ) {
		vec3 absDirection = abs( direction );
		float face = - 1.0;
		if ( absDirection.x > absDirection.z ) {
			if ( absDirection.x > absDirection.y )
				face = direction.x > 0.0 ? 0.0 : 3.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		} else {
			if ( absDirection.z > absDirection.y )
				face = direction.z > 0.0 ? 2.0 : 5.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		}
		return face;
	}
	vec2 getUV( vec3 direction, float face ) {
		vec2 uv;
		if ( face == 0.0 ) {
			uv = vec2( direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 1.0 ) {
			uv = vec2( - direction.x, - direction.z ) / abs( direction.y );
		} else if ( face == 2.0 ) {
			uv = vec2( - direction.x, direction.y ) / abs( direction.z );
		} else if ( face == 3.0 ) {
			uv = vec2( - direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 4.0 ) {
			uv = vec2( - direction.x, direction.z ) / abs( direction.y );
		} else {
			uv = vec2( direction.x, direction.y ) / abs( direction.z );
		}
		return 0.5 * ( uv + 1.0 );
	}
	vec3 bilinearCubeUV( sampler2D envMap, vec3 direction, float mipInt ) {
		float face = getFace( direction );
		float filterInt = max( cubeUV_minMipLevel - mipInt, 0.0 );
		mipInt = max( mipInt, cubeUV_minMipLevel );
		float faceSize = exp2( mipInt );
		highp vec2 uv = getUV( direction, face ) * ( faceSize - 2.0 ) + 1.0;
		if ( face > 2.0 ) {
			uv.y += faceSize;
			face -= 3.0;
		}
		uv.x += face * faceSize;
		uv.x += filterInt * 3.0 * cubeUV_minTileSize;
		uv.y += 4.0 * ( exp2( CUBEUV_MAX_MIP ) - faceSize );
		uv.x *= CUBEUV_TEXEL_WIDTH;
		uv.y *= CUBEUV_TEXEL_HEIGHT;
		#ifdef texture2DGradEXT
			return texture2DGradEXT( envMap, uv, vec2( 0.0 ), vec2( 0.0 ) ).rgb;
		#else
			return texture2D( envMap, uv ).rgb;
		#endif
	}
	#define cubeUV_r0 1.0
	#define cubeUV_m0 - 2.0
	#define cubeUV_r1 0.8
	#define cubeUV_m1 - 1.0
	#define cubeUV_r4 0.4
	#define cubeUV_m4 2.0
	#define cubeUV_r5 0.305
	#define cubeUV_m5 3.0
	#define cubeUV_r6 0.21
	#define cubeUV_m6 4.0
	float roughnessToMip( float roughness ) {
		float mip = 0.0;
		if ( roughness >= cubeUV_r1 ) {
			mip = ( cubeUV_r0 - roughness ) * ( cubeUV_m1 - cubeUV_m0 ) / ( cubeUV_r0 - cubeUV_r1 ) + cubeUV_m0;
		} else if ( roughness >= cubeUV_r4 ) {
			mip = ( cubeUV_r1 - roughness ) * ( cubeUV_m4 - cubeUV_m1 ) / ( cubeUV_r1 - cubeUV_r4 ) + cubeUV_m1;
		} else if ( roughness >= cubeUV_r5 ) {
			mip = ( cubeUV_r4 - roughness ) * ( cubeUV_m5 - cubeUV_m4 ) / ( cubeUV_r4 - cubeUV_r5 ) + cubeUV_m4;
		} else if ( roughness >= cubeUV_r6 ) {
			mip = ( cubeUV_r5 - roughness ) * ( cubeUV_m6 - cubeUV_m5 ) / ( cubeUV_r5 - cubeUV_r6 ) + cubeUV_m5;
		} else {
			mip = - 2.0 * log2( 1.16 * roughness );		}
		return mip;
	}
	vec4 textureCubeUV( sampler2D envMap, vec3 sampleDir, float roughness ) {
		float mip = clamp( roughnessToMip( roughness ), cubeUV_m0, CUBEUV_MAX_MIP );
		float mipF = fract( mip );
		float mipInt = floor( mip );
		vec3 color0 = bilinearCubeUV( envMap, sampleDir, mipInt );
		if ( mipF == 0.0 ) {
			return vec4( color0, 1.0 );
		} else {
			vec3 color1 = bilinearCubeUV( envMap, sampleDir, mipInt + 1.0 );
			return vec4( mix( color0, color1, mipF ), 1.0 );
		}
	}
#endif`,c5=`vec3 transformedNormal = objectNormal;
#ifdef USE_TANGENT
	vec3 transformedTangent = objectTangent;
#endif
#ifdef USE_BATCHING
	mat3 bm = mat3( batchingMatrix );
	transformedNormal /= vec3( dot( bm[ 0 ], bm[ 0 ] ), dot( bm[ 1 ], bm[ 1 ] ), dot( bm[ 2 ], bm[ 2 ] ) );
	transformedNormal = bm * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = bm * transformedTangent;
	#endif
#endif
#ifdef USE_INSTANCING
	mat3 im = mat3( instanceMatrix );
	transformedNormal /= vec3( dot( im[ 0 ], im[ 0 ] ), dot( im[ 1 ], im[ 1 ] ), dot( im[ 2 ], im[ 2 ] ) );
	transformedNormal = im * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = im * transformedTangent;
	#endif
#endif
transformedNormal = normalMatrix * transformedNormal;
#ifdef FLIP_SIDED
	transformedNormal = - transformedNormal;
#endif
#ifdef USE_TANGENT
	transformedTangent = ( modelViewMatrix * vec4( transformedTangent, 0.0 ) ).xyz;
	#ifdef FLIP_SIDED
		transformedTangent = - transformedTangent;
	#endif
#endif`,n5=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,s5=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,i5=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,o5=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,a5="gl_FragColor = linearToOutputTexel( gl_FragColor );",r5=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,t5=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vec3 cameraToFrag;
		if ( isOrthographic ) {
			cameraToFrag = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToFrag = normalize( vWorldPosition - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vec3 reflectVec = reflect( cameraToFrag, worldNormal );
		#else
			vec3 reflectVec = refract( cameraToFrag, worldNormal, refractionRatio );
		#endif
	#else
		vec3 reflectVec = vReflect;
	#endif
	#ifdef ENVMAP_TYPE_CUBE
		vec4 envColor = textureCube( envMap, envMapRotation * vec3( flipEnvMap * reflectVec.x, reflectVec.yz ) );
	#else
		vec4 envColor = vec4( 0.0 );
	#endif
	#ifdef ENVMAP_BLENDING_MULTIPLY
		outgoingLight = mix( outgoingLight, outgoingLight * envColor.xyz, specularStrength * reflectivity );
	#elif defined( ENVMAP_BLENDING_MIX )
		outgoingLight = mix( outgoingLight, envColor.xyz, specularStrength * reflectivity );
	#elif defined( ENVMAP_BLENDING_ADD )
		outgoingLight += envColor.xyz * specularStrength * reflectivity;
	#endif
#endif`,e5=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform float flipEnvMap;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
	
#endif`,JQ=`#ifdef USE_ENVMAP
	uniform float reflectivity;
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		varying vec3 vWorldPosition;
		uniform float refractionRatio;
	#else
		varying vec3 vReflect;
	#endif
#endif`,$Q=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,QQ=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vWorldPosition = worldPosition.xyz;
	#else
		vec3 cameraToVertex;
		if ( isOrthographic ) {
			cameraToVertex = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToVertex = normalize( worldPosition.xyz - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vReflect = reflect( cameraToVertex, worldNormal );
		#else
			vReflect = refract( cameraToVertex, worldNormal, refractionRatio );
		#endif
	#endif
#endif`,ZQ=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,WQ=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,YQ=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,HQ=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,XQ=`#ifdef USE_GRADIENTMAP
	uniform sampler2D gradientMap;
#endif
vec3 getGradientIrradiance( vec3 normal, vec3 lightDirection ) {
	float dotNL = dot( normal, lightDirection );
	vec2 coord = vec2( dotNL * 0.5 + 0.5, 0.0 );
	#ifdef USE_GRADIENTMAP
		return vec3( texture2D( gradientMap, coord ).r );
	#else
		vec2 fw = fwidth( coord ) * 0.5;
		return mix( vec3( 0.7 ), vec3( 1.0 ), smoothstep( 0.7 - fw.x, 0.7 + fw.x, coord.x ) );
	#endif
}`,KQ=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,GQ=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,UQ=`varying vec3 vViewPosition;
struct LambertMaterial {
	vec3 diffuseColor;
	float specularStrength;
};
void RE_Direct_Lambert( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Lambert( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Lambert
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,qQ=`uniform bool receiveShadow;
uniform vec3 ambientLightColor;
#if defined( USE_LIGHT_PROBES )
	uniform vec3 lightProbe[ 9 ];
#endif
vec3 shGetIrradianceAt( in vec3 normal, in vec3 shCoefficients[ 9 ] ) {
	float x = normal.x, y = normal.y, z = normal.z;
	vec3 result = shCoefficients[ 0 ] * 0.886227;
	result += shCoefficients[ 1 ] * 2.0 * 0.511664 * y;
	result += shCoefficients[ 2 ] * 2.0 * 0.511664 * z;
	result += shCoefficients[ 3 ] * 2.0 * 0.511664 * x;
	result += shCoefficients[ 4 ] * 2.0 * 0.429043 * x * y;
	result += shCoefficients[ 5 ] * 2.0 * 0.429043 * y * z;
	result += shCoefficients[ 6 ] * ( 0.743125 * z * z - 0.247708 );
	result += shCoefficients[ 7 ] * 2.0 * 0.429043 * x * z;
	result += shCoefficients[ 8 ] * 0.429043 * ( x * x - y * y );
	return result;
}
vec3 getLightProbeIrradiance( const in vec3 lightProbe[ 9 ], const in vec3 normal ) {
	vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
	vec3 irradiance = shGetIrradianceAt( worldNormal, lightProbe );
	return irradiance;
}
vec3 getAmbientLightIrradiance( const in vec3 ambientLightColor ) {
	vec3 irradiance = ambientLightColor;
	return irradiance;
}
float getDistanceAttenuation( const in float lightDistance, const in float cutoffDistance, const in float decayExponent ) {
	float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );
	if ( cutoffDistance > 0.0 ) {
		distanceFalloff *= pow2( saturate( 1.0 - pow4( lightDistance / cutoffDistance ) ) );
	}
	return distanceFalloff;
}
float getSpotAttenuation( const in float coneCosine, const in float penumbraCosine, const in float angleCosine ) {
	return smoothstep( coneCosine, penumbraCosine, angleCosine );
}
#if NUM_DIR_LIGHTS > 0
	struct DirectionalLight {
		vec3 direction;
		vec3 color;
	};
	uniform DirectionalLight directionalLights[ NUM_DIR_LIGHTS ];
	void getDirectionalLightInfo( const in DirectionalLight directionalLight, out IncidentLight light ) {
		light.color = directionalLight.color;
		light.direction = directionalLight.direction;
		light.visible = true;
	}
#endif
#if NUM_POINT_LIGHTS > 0
	struct PointLight {
		vec3 position;
		vec3 color;
		float distance;
		float decay;
	};
	uniform PointLight pointLights[ NUM_POINT_LIGHTS ];
	void getPointLightInfo( const in PointLight pointLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = pointLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float lightDistance = length( lVector );
		light.color = pointLight.color;
		light.color *= getDistanceAttenuation( lightDistance, pointLight.distance, pointLight.decay );
		light.visible = ( light.color != vec3( 0.0 ) );
	}
#endif
#if NUM_SPOT_LIGHTS > 0
	struct SpotLight {
		vec3 position;
		vec3 direction;
		vec3 color;
		float distance;
		float decay;
		float coneCos;
		float penumbraCos;
	};
	uniform SpotLight spotLights[ NUM_SPOT_LIGHTS ];
	void getSpotLightInfo( const in SpotLight spotLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = spotLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float angleCos = dot( light.direction, spotLight.direction );
		float spotAttenuation = getSpotAttenuation( spotLight.coneCos, spotLight.penumbraCos, angleCos );
		if ( spotAttenuation > 0.0 ) {
			float lightDistance = length( lVector );
			light.color = spotLight.color * spotAttenuation;
			light.color *= getDistanceAttenuation( lightDistance, spotLight.distance, spotLight.decay );
			light.visible = ( light.color != vec3( 0.0 ) );
		} else {
			light.color = vec3( 0.0 );
			light.visible = false;
		}
	}
#endif
#if NUM_RECT_AREA_LIGHTS > 0
	struct RectAreaLight {
		vec3 color;
		vec3 position;
		vec3 halfWidth;
		vec3 halfHeight;
	};
	uniform sampler2D ltc_1;	uniform sampler2D ltc_2;
	uniform RectAreaLight rectAreaLights[ NUM_RECT_AREA_LIGHTS ];
#endif
#if NUM_HEMI_LIGHTS > 0
	struct HemisphereLight {
		vec3 direction;
		vec3 skyColor;
		vec3 groundColor;
	};
	uniform HemisphereLight hemisphereLights[ NUM_HEMI_LIGHTS ];
	vec3 getHemisphereLightIrradiance( const in HemisphereLight hemiLight, const in vec3 normal ) {
		float dotNL = dot( normal, hemiLight.direction );
		float hemiDiffuseWeight = 0.5 * dotNL + 0.5;
		vec3 irradiance = mix( hemiLight.groundColor, hemiLight.skyColor, hemiDiffuseWeight );
		return irradiance;
	}
#endif`,EQ=`#ifdef USE_ENVMAP
	vec3 getIBLIrradiance( const in vec3 normal ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * worldNormal, 1.0 );
			return PI * envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	vec3 getIBLRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 reflectVec = reflect( - viewDir, normal );
			reflectVec = normalize( mix( reflectVec, normal, roughness * roughness) );
			reflectVec = inverseTransformDirection( reflectVec, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * reflectVec, roughness );
			return envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	#ifdef USE_ANISOTROPY
		vec3 getIBLAnisotropyRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 bentNormal = cross( bitangent, viewDir );
				bentNormal = normalize( cross( bentNormal, bitangent ) );
				bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
				return getIBLRadiance( viewDir, bentNormal, roughness );
			#else
				return vec3( 0.0 );
			#endif
		}
	#endif
#endif`,VQ=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,FQ=`varying vec3 vViewPosition;
struct ToonMaterial {
	vec3 diffuseColor;
};
void RE_Direct_Toon( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 irradiance = getGradientIrradiance( geometryNormal, directLight.direction ) * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Toon( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Toon
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,DQ=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,RQ=`varying vec3 vViewPosition;
struct BlinnPhongMaterial {
	vec3 diffuseColor;
	vec3 specularColor;
	float specularShininess;
	float specularStrength;
};
void RE_Direct_BlinnPhong( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
	reflectedLight.directSpecular += irradiance * BRDF_BlinnPhong( directLight.direction, geometryViewDir, geometryNormal, material.specularColor, material.specularShininess ) * material.specularStrength;
}
void RE_IndirectDiffuse_BlinnPhong( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_BlinnPhong
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,NQ=`PhysicalMaterial material;
material.diffuseColor = diffuseColor.rgb * ( 1.0 - metalnessFactor );
vec3 dxy = max( abs( dFdx( nonPerturbedNormal ) ), abs( dFdy( nonPerturbedNormal ) ) );
float geometryRoughness = max( max( dxy.x, dxy.y ), dxy.z );
material.roughness = max( roughnessFactor, 0.0525 );material.roughness += geometryRoughness;
material.roughness = min( material.roughness, 1.0 );
#ifdef IOR
	material.ior = ior;
	#ifdef USE_SPECULAR
		float specularIntensityFactor = specularIntensity;
		vec3 specularColorFactor = specularColor;
		#ifdef USE_SPECULAR_COLORMAP
			specularColorFactor *= texture2D( specularColorMap, vSpecularColorMapUv ).rgb;
		#endif
		#ifdef USE_SPECULAR_INTENSITYMAP
			specularIntensityFactor *= texture2D( specularIntensityMap, vSpecularIntensityMapUv ).a;
		#endif
		material.specularF90 = mix( specularIntensityFactor, 1.0, metalnessFactor );
	#else
		float specularIntensityFactor = 1.0;
		vec3 specularColorFactor = vec3( 1.0 );
		material.specularF90 = 1.0;
	#endif
	material.specularColor = mix( min( pow2( ( material.ior - 1.0 ) / ( material.ior + 1.0 ) ) * specularColorFactor, vec3( 1.0 ) ) * specularIntensityFactor, diffuseColor.rgb, metalnessFactor );
#else
	material.specularColor = mix( vec3( 0.04 ), diffuseColor.rgb, metalnessFactor );
	material.specularF90 = 1.0;
#endif
#ifdef USE_CLEARCOAT
	material.clearcoat = clearcoat;
	material.clearcoatRoughness = clearcoatRoughness;
	material.clearcoatF0 = vec3( 0.04 );
	material.clearcoatF90 = 1.0;
	#ifdef USE_CLEARCOATMAP
		material.clearcoat *= texture2D( clearcoatMap, vClearcoatMapUv ).x;
	#endif
	#ifdef USE_CLEARCOAT_ROUGHNESSMAP
		material.clearcoatRoughness *= texture2D( clearcoatRoughnessMap, vClearcoatRoughnessMapUv ).y;
	#endif
	material.clearcoat = saturate( material.clearcoat );	material.clearcoatRoughness = max( material.clearcoatRoughness, 0.0525 );
	material.clearcoatRoughness += geometryRoughness;
	material.clearcoatRoughness = min( material.clearcoatRoughness, 1.0 );
#endif
#ifdef USE_DISPERSION
	material.dispersion = dispersion;
#endif
#ifdef USE_IRIDESCENCE
	material.iridescence = iridescence;
	material.iridescenceIOR = iridescenceIOR;
	#ifdef USE_IRIDESCENCEMAP
		material.iridescence *= texture2D( iridescenceMap, vIridescenceMapUv ).r;
	#endif
	#ifdef USE_IRIDESCENCE_THICKNESSMAP
		material.iridescenceThickness = (iridescenceThicknessMaximum - iridescenceThicknessMinimum) * texture2D( iridescenceThicknessMap, vIridescenceThicknessMapUv ).g + iridescenceThicknessMinimum;
	#else
		material.iridescenceThickness = iridescenceThicknessMaximum;
	#endif
#endif
#ifdef USE_SHEEN
	material.sheenColor = sheenColor;
	#ifdef USE_SHEEN_COLORMAP
		material.sheenColor *= texture2D( sheenColorMap, vSheenColorMapUv ).rgb;
	#endif
	material.sheenRoughness = clamp( sheenRoughness, 0.07, 1.0 );
	#ifdef USE_SHEEN_ROUGHNESSMAP
		material.sheenRoughness *= texture2D( sheenRoughnessMap, vSheenRoughnessMapUv ).a;
	#endif
#endif
#ifdef USE_ANISOTROPY
	#ifdef USE_ANISOTROPYMAP
		mat2 anisotropyMat = mat2( anisotropyVector.x, anisotropyVector.y, - anisotropyVector.y, anisotropyVector.x );
		vec3 anisotropyPolar = texture2D( anisotropyMap, vAnisotropyMapUv ).rgb;
		vec2 anisotropyV = anisotropyMat * normalize( 2.0 * anisotropyPolar.rg - vec2( 1.0 ) ) * anisotropyPolar.b;
	#else
		vec2 anisotropyV = anisotropyVector;
	#endif
	material.anisotropy = length( anisotropyV );
	if( material.anisotropy == 0.0 ) {
		anisotropyV = vec2( 1.0, 0.0 );
	} else {
		anisotropyV /= material.anisotropy;
		material.anisotropy = saturate( material.anisotropy );
	}
	material.alphaT = mix( pow2( material.roughness ), 1.0, pow2( material.anisotropy ) );
	material.anisotropyT = tbn[ 0 ] * anisotropyV.x + tbn[ 1 ] * anisotropyV.y;
	material.anisotropyB = tbn[ 1 ] * anisotropyV.x - tbn[ 0 ] * anisotropyV.y;
#endif`,OQ=`struct PhysicalMaterial {
	vec3 diffuseColor;
	float roughness;
	vec3 specularColor;
	float specularF90;
	float dispersion;
	#ifdef USE_CLEARCOAT
		float clearcoat;
		float clearcoatRoughness;
		vec3 clearcoatF0;
		float clearcoatF90;
	#endif
	#ifdef USE_IRIDESCENCE
		float iridescence;
		float iridescenceIOR;
		float iridescenceThickness;
		vec3 iridescenceFresnel;
		vec3 iridescenceF0;
	#endif
	#ifdef USE_SHEEN
		vec3 sheenColor;
		float sheenRoughness;
	#endif
	#ifdef IOR
		float ior;
	#endif
	#ifdef USE_TRANSMISSION
		float transmission;
		float transmissionAlpha;
		float thickness;
		float attenuationDistance;
		vec3 attenuationColor;
	#endif
	#ifdef USE_ANISOTROPY
		float anisotropy;
		float alphaT;
		vec3 anisotropyT;
		vec3 anisotropyB;
	#endif
};
vec3 clearcoatSpecularDirect = vec3( 0.0 );
vec3 clearcoatSpecularIndirect = vec3( 0.0 );
vec3 sheenSpecularDirect = vec3( 0.0 );
vec3 sheenSpecularIndirect = vec3(0.0 );
vec3 Schlick_to_F0( const in vec3 f, const in float f90, const in float dotVH ) {
    float x = clamp( 1.0 - dotVH, 0.0, 1.0 );
    float x2 = x * x;
    float x5 = clamp( x * x2 * x2, 0.0, 0.9999 );
    return ( f - vec3( f90 ) * x5 ) / ( 1.0 - x5 );
}
float V_GGX_SmithCorrelated( const in float alpha, const in float dotNL, const in float dotNV ) {
	float a2 = pow2( alpha );
	float gv = dotNL * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNV ) );
	float gl = dotNV * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNL ) );
	return 0.5 / max( gv + gl, EPSILON );
}
float D_GGX( const in float alpha, const in float dotNH ) {
	float a2 = pow2( alpha );
	float denom = pow2( dotNH ) * ( a2 - 1.0 ) + 1.0;
	return RECIPROCAL_PI * a2 / pow2( denom );
}
#ifdef USE_ANISOTROPY
	float V_GGX_SmithCorrelated_Anisotropic( const in float alphaT, const in float alphaB, const in float dotTV, const in float dotBV, const in float dotTL, const in float dotBL, const in float dotNV, const in float dotNL ) {
		float gv = dotNL * length( vec3( alphaT * dotTV, alphaB * dotBV, dotNV ) );
		float gl = dotNV * length( vec3( alphaT * dotTL, alphaB * dotBL, dotNL ) );
		float v = 0.5 / ( gv + gl );
		return saturate(v);
	}
	float D_GGX_Anisotropic( const in float alphaT, const in float alphaB, const in float dotNH, const in float dotTH, const in float dotBH ) {
		float a2 = alphaT * alphaB;
		highp vec3 v = vec3( alphaB * dotTH, alphaT * dotBH, a2 * dotNH );
		highp float v2 = dot( v, v );
		float w2 = a2 / v2;
		return RECIPROCAL_PI * a2 * pow2 ( w2 );
	}
#endif
#ifdef USE_CLEARCOAT
	vec3 BRDF_GGX_Clearcoat( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material) {
		vec3 f0 = material.clearcoatF0;
		float f90 = material.clearcoatF90;
		float roughness = material.clearcoatRoughness;
		float alpha = pow2( roughness );
		vec3 halfDir = normalize( lightDir + viewDir );
		float dotNL = saturate( dot( normal, lightDir ) );
		float dotNV = saturate( dot( normal, viewDir ) );
		float dotNH = saturate( dot( normal, halfDir ) );
		float dotVH = saturate( dot( viewDir, halfDir ) );
		vec3 F = F_Schlick( f0, f90, dotVH );
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
		return F * ( V * D );
	}
#endif
vec3 BRDF_GGX( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 f0 = material.specularColor;
	float f90 = material.specularF90;
	float roughness = material.roughness;
	float alpha = pow2( roughness );
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( f0, f90, dotVH );
	#ifdef USE_IRIDESCENCE
		F = mix( F, material.iridescenceFresnel, material.iridescence );
	#endif
	#ifdef USE_ANISOTROPY
		float dotTL = dot( material.anisotropyT, lightDir );
		float dotTV = dot( material.anisotropyT, viewDir );
		float dotTH = dot( material.anisotropyT, halfDir );
		float dotBL = dot( material.anisotropyB, lightDir );
		float dotBV = dot( material.anisotropyB, viewDir );
		float dotBH = dot( material.anisotropyB, halfDir );
		float V = V_GGX_SmithCorrelated_Anisotropic( material.alphaT, alpha, dotTV, dotBV, dotTL, dotBL, dotNV, dotNL );
		float D = D_GGX_Anisotropic( material.alphaT, alpha, dotNH, dotTH, dotBH );
	#else
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
	#endif
	return F * ( V * D );
}
vec2 LTC_Uv( const in vec3 N, const in vec3 V, const in float roughness ) {
	const float LUT_SIZE = 64.0;
	const float LUT_SCALE = ( LUT_SIZE - 1.0 ) / LUT_SIZE;
	const float LUT_BIAS = 0.5 / LUT_SIZE;
	float dotNV = saturate( dot( N, V ) );
	vec2 uv = vec2( roughness, sqrt( 1.0 - dotNV ) );
	uv = uv * LUT_SCALE + LUT_BIAS;
	return uv;
}
float LTC_ClippedSphereFormFactor( const in vec3 f ) {
	float l = length( f );
	return max( ( l * l + f.z ) / ( l + 1.0 ), 0.0 );
}
vec3 LTC_EdgeVectorFormFactor( const in vec3 v1, const in vec3 v2 ) {
	float x = dot( v1, v2 );
	float y = abs( x );
	float a = 0.8543985 + ( 0.4965155 + 0.0145206 * y ) * y;
	float b = 3.4175940 + ( 4.1616724 + y ) * y;
	float v = a / b;
	float theta_sintheta = ( x > 0.0 ) ? v : 0.5 * inversesqrt( max( 1.0 - x * x, 1e-7 ) ) - v;
	return cross( v1, v2 ) * theta_sintheta;
}
vec3 LTC_Evaluate( const in vec3 N, const in vec3 V, const in vec3 P, const in mat3 mInv, const in vec3 rectCoords[ 4 ] ) {
	vec3 v1 = rectCoords[ 1 ] - rectCoords[ 0 ];
	vec3 v2 = rectCoords[ 3 ] - rectCoords[ 0 ];
	vec3 lightNormal = cross( v1, v2 );
	if( dot( lightNormal, P - rectCoords[ 0 ] ) < 0.0 ) return vec3( 0.0 );
	vec3 T1, T2;
	T1 = normalize( V - N * dot( V, N ) );
	T2 = - cross( N, T1 );
	mat3 mat = mInv * transposeMat3( mat3( T1, T2, N ) );
	vec3 coords[ 4 ];
	coords[ 0 ] = mat * ( rectCoords[ 0 ] - P );
	coords[ 1 ] = mat * ( rectCoords[ 1 ] - P );
	coords[ 2 ] = mat * ( rectCoords[ 2 ] - P );
	coords[ 3 ] = mat * ( rectCoords[ 3 ] - P );
	coords[ 0 ] = normalize( coords[ 0 ] );
	coords[ 1 ] = normalize( coords[ 1 ] );
	coords[ 2 ] = normalize( coords[ 2 ] );
	coords[ 3 ] = normalize( coords[ 3 ] );
	vec3 vectorFormFactor = vec3( 0.0 );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 0 ], coords[ 1 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 1 ], coords[ 2 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 2 ], coords[ 3 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 3 ], coords[ 0 ] );
	float result = LTC_ClippedSphereFormFactor( vectorFormFactor );
	return vec3( result );
}
#if defined( USE_SHEEN )
float D_Charlie( float roughness, float dotNH ) {
	float alpha = pow2( roughness );
	float invAlpha = 1.0 / alpha;
	float cos2h = dotNH * dotNH;
	float sin2h = max( 1.0 - cos2h, 0.0078125 );
	return ( 2.0 + invAlpha ) * pow( sin2h, invAlpha * 0.5 ) / ( 2.0 * PI );
}
float V_Neubelt( float dotNV, float dotNL ) {
	return saturate( 1.0 / ( 4.0 * ( dotNL + dotNV - dotNL * dotNV ) ) );
}
vec3 BRDF_Sheen( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, vec3 sheenColor, const in float sheenRoughness ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float D = D_Charlie( sheenRoughness, dotNH );
	float V = V_Neubelt( dotNV, dotNL );
	return sheenColor * ( D * V );
}
#endif
float IBLSheenBRDF( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	float r2 = roughness * roughness;
	float a = roughness < 0.25 ? -339.2 * r2 + 161.4 * roughness - 25.9 : -8.48 * r2 + 14.3 * roughness - 9.95;
	float b = roughness < 0.25 ? 44.0 * r2 - 23.7 * roughness + 3.26 : 1.97 * r2 - 3.27 * roughness + 0.72;
	float DG = exp( a * dotNV + b ) + ( roughness < 0.25 ? 0.0 : 0.1 * ( roughness - 0.25 ) );
	return saturate( DG * RECIPROCAL_PI );
}
vec2 DFGApprox( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	const vec4 c0 = vec4( - 1, - 0.0275, - 0.572, 0.022 );
	const vec4 c1 = vec4( 1, 0.0425, 1.04, - 0.04 );
	vec4 r = roughness * c0 + c1;
	float a004 = min( r.x * r.x, exp2( - 9.28 * dotNV ) ) * r.x + r.y;
	vec2 fab = vec2( - 1.04, 1.04 ) * a004 + r.zw;
	return fab;
}
vec3 EnvironmentBRDF( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness ) {
	vec2 fab = DFGApprox( normal, viewDir, roughness );
	return specularColor * fab.x + specularF90 * fab.y;
}
#ifdef USE_IRIDESCENCE
void computeMultiscatteringIridescence( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float iridescence, const in vec3 iridescenceF0, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#else
void computeMultiscattering( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#endif
	vec2 fab = DFGApprox( normal, viewDir, roughness );
	#ifdef USE_IRIDESCENCE
		vec3 Fr = mix( specularColor, iridescenceF0, iridescence );
	#else
		vec3 Fr = specularColor;
	#endif
	vec3 FssEss = Fr * fab.x + specularF90 * fab.y;
	float Ess = fab.x + fab.y;
	float Ems = 1.0 - Ess;
	vec3 Favg = Fr + ( 1.0 - Fr ) * 0.047619;	vec3 Fms = FssEss * Favg / ( 1.0 - Ems * Favg );
	singleScatter += FssEss;
	multiScatter += Fms * Ems;
}
#if NUM_RECT_AREA_LIGHTS > 0
	void RE_Direct_RectArea_Physical( const in RectAreaLight rectAreaLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
		vec3 normal = geometryNormal;
		vec3 viewDir = geometryViewDir;
		vec3 position = geometryPosition;
		vec3 lightPos = rectAreaLight.position;
		vec3 halfWidth = rectAreaLight.halfWidth;
		vec3 halfHeight = rectAreaLight.halfHeight;
		vec3 lightColor = rectAreaLight.color;
		float roughness = material.roughness;
		vec3 rectCoords[ 4 ];
		rectCoords[ 0 ] = lightPos + halfWidth - halfHeight;		rectCoords[ 1 ] = lightPos - halfWidth - halfHeight;
		rectCoords[ 2 ] = lightPos - halfWidth + halfHeight;
		rectCoords[ 3 ] = lightPos + halfWidth + halfHeight;
		vec2 uv = LTC_Uv( normal, viewDir, roughness );
		vec4 t1 = texture2D( ltc_1, uv );
		vec4 t2 = texture2D( ltc_2, uv );
		mat3 mInv = mat3(
			vec3( t1.x, 0, t1.y ),
			vec3(    0, 1,    0 ),
			vec3( t1.z, 0, t1.w )
		);
		vec3 fresnel = ( material.specularColor * t2.x + ( vec3( 1.0 ) - material.specularColor ) * t2.y );
		reflectedLight.directSpecular += lightColor * fresnel * LTC_Evaluate( normal, viewDir, position, mInv, rectCoords );
		reflectedLight.directDiffuse += lightColor * material.diffuseColor * LTC_Evaluate( normal, viewDir, position, mat3( 1.0 ), rectCoords );
	}
#endif
void RE_Direct_Physical( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	#ifdef USE_CLEARCOAT
		float dotNLcc = saturate( dot( geometryClearcoatNormal, directLight.direction ) );
		vec3 ccIrradiance = dotNLcc * directLight.color;
		clearcoatSpecularDirect += ccIrradiance * BRDF_GGX_Clearcoat( directLight.direction, geometryViewDir, geometryClearcoatNormal, material );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularDirect += irradiance * BRDF_Sheen( directLight.direction, geometryViewDir, geometryNormal, material.sheenColor, material.sheenRoughness );
	#endif
	reflectedLight.directSpecular += irradiance * BRDF_GGX( directLight.direction, geometryViewDir, geometryNormal, material );
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Physical( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectSpecular_Physical( const in vec3 radiance, const in vec3 irradiance, const in vec3 clearcoatRadiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
	#ifdef USE_CLEARCOAT
		clearcoatSpecularIndirect += clearcoatRadiance * EnvironmentBRDF( geometryClearcoatNormal, geometryViewDir, material.clearcoatF0, material.clearcoatF90, material.clearcoatRoughness );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularIndirect += irradiance * material.sheenColor * IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
	#endif
	vec3 singleScattering = vec3( 0.0 );
	vec3 multiScattering = vec3( 0.0 );
	vec3 cosineWeightedIrradiance = irradiance * RECIPROCAL_PI;
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.iridescence, material.iridescenceFresnel, material.roughness, singleScattering, multiScattering );
	#else
		computeMultiscattering( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.roughness, singleScattering, multiScattering );
	#endif
	vec3 totalScattering = singleScattering + multiScattering;
	vec3 diffuse = material.diffuseColor * ( 1.0 - max( max( totalScattering.r, totalScattering.g ), totalScattering.b ) );
	reflectedLight.indirectSpecular += radiance * singleScattering;
	reflectedLight.indirectSpecular += multiScattering * cosineWeightedIrradiance;
	reflectedLight.indirectDiffuse += diffuse * cosineWeightedIrradiance;
}
#define RE_Direct				RE_Direct_Physical
#define RE_Direct_RectArea		RE_Direct_RectArea_Physical
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Physical
#define RE_IndirectSpecular		RE_IndirectSpecular_Physical
float computeSpecularOcclusion( const in float dotNV, const in float ambientOcclusion, const in float roughness ) {
	return saturate( pow( dotNV + ambientOcclusion, exp2( - 16.0 * roughness - 1.0 ) ) - 1.0 + ambientOcclusion );
}`,MQ=`
vec3 geometryPosition = - vViewPosition;
vec3 geometryNormal = normal;
vec3 geometryViewDir = ( isOrthographic ) ? vec3( 0, 0, 1 ) : normalize( vViewPosition );
vec3 geometryClearcoatNormal = vec3( 0.0 );
#ifdef USE_CLEARCOAT
	geometryClearcoatNormal = clearcoatNormal;
#endif
#ifdef USE_IRIDESCENCE
	float dotNVi = saturate( dot( normal, geometryViewDir ) );
	if ( material.iridescenceThickness == 0.0 ) {
		material.iridescence = 0.0;
	} else {
		material.iridescence = saturate( material.iridescence );
	}
	if ( material.iridescence > 0.0 ) {
		material.iridescenceFresnel = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.specularColor );
		material.iridescenceF0 = Schlick_to_F0( material.iridescenceFresnel, 1.0, dotNVi );
	}
#endif
IncidentLight directLight;
#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )
	PointLight pointLight;
	#if defined( USE_SHADOWMAP ) && NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHTS; i ++ ) {
		pointLight = pointLights[ i ];
		getPointLightInfo( pointLight, geometryPosition, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_POINT_LIGHT_SHADOWS )
		pointLightShadow = pointLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getPointShadow( pointShadowMap[ i ], pointLightShadow.shadowMapSize, pointLightShadow.shadowIntensity, pointLightShadow.shadowBias, pointLightShadow.shadowRadius, vPointShadowCoord[ i ], pointLightShadow.shadowCameraNear, pointLightShadow.shadowCameraFar ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SPOT_LIGHTS > 0 ) && defined( RE_Direct )
	SpotLight spotLight;
	vec4 spotColor;
	vec3 spotLightCoord;
	bool inSpotLightMap;
	#if defined( USE_SHADOWMAP ) && NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHTS; i ++ ) {
		spotLight = spotLights[ i ];
		getSpotLightInfo( spotLight, geometryPosition, directLight );
		#if ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#define SPOT_LIGHT_MAP_INDEX UNROLLED_LOOP_INDEX
		#elif ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		#define SPOT_LIGHT_MAP_INDEX NUM_SPOT_LIGHT_MAPS
		#else
		#define SPOT_LIGHT_MAP_INDEX ( UNROLLED_LOOP_INDEX - NUM_SPOT_LIGHT_SHADOWS + NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#endif
		#if ( SPOT_LIGHT_MAP_INDEX < NUM_SPOT_LIGHT_MAPS )
			spotLightCoord = vSpotLightCoord[ i ].xyz / vSpotLightCoord[ i ].w;
			inSpotLightMap = all( lessThan( abs( spotLightCoord * 2. - 1. ), vec3( 1.0 ) ) );
			spotColor = texture2D( spotLightMap[ SPOT_LIGHT_MAP_INDEX ], spotLightCoord.xy );
			directLight.color = inSpotLightMap ? directLight.color * spotColor.rgb : directLight.color;
		#endif
		#undef SPOT_LIGHT_MAP_INDEX
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		spotLightShadow = spotLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( spotShadowMap[ i ], spotLightShadow.shadowMapSize, spotLightShadow.shadowIntensity, spotLightShadow.shadowBias, spotLightShadow.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_DIR_LIGHTS > 0 ) && defined( RE_Direct )
	DirectionalLight directionalLight;
	#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHTS; i ++ ) {
		directionalLight = directionalLights[ i ];
		getDirectionalLightInfo( directionalLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_DIR_LIGHT_SHADOWS )
		directionalLightShadow = directionalLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( directionalShadowMap[ i ], directionalLightShadow.shadowMapSize, directionalLightShadow.shadowIntensity, directionalLightShadow.shadowBias, directionalLightShadow.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_RECT_AREA_LIGHTS > 0 ) && defined( RE_Direct_RectArea )
	RectAreaLight rectAreaLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_RECT_AREA_LIGHTS; i ++ ) {
		rectAreaLight = rectAreaLights[ i ];
		RE_Direct_RectArea( rectAreaLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if defined( RE_IndirectDiffuse )
	vec3 iblIrradiance = vec3( 0.0 );
	vec3 irradiance = getAmbientLightIrradiance( ambientLightColor );
	#if defined( USE_LIGHT_PROBES )
		irradiance += getLightProbeIrradiance( lightProbe, geometryNormal );
	#endif
	#if ( NUM_HEMI_LIGHTS > 0 )
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_HEMI_LIGHTS; i ++ ) {
			irradiance += getHemisphereLightIrradiance( hemisphereLights[ i ], geometryNormal );
		}
		#pragma unroll_loop_end
	#endif
#endif
#if defined( RE_IndirectSpecular )
	vec3 radiance = vec3( 0.0 );
	vec3 clearcoatRadiance = vec3( 0.0 );
#endif`,BQ=`#if defined( RE_IndirectDiffuse )
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		vec3 lightMapIrradiance = lightMapTexel.rgb * lightMapIntensity;
		irradiance += lightMapIrradiance;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD ) && defined( ENVMAP_TYPE_CUBE_UV )
		iblIrradiance += getIBLIrradiance( geometryNormal );
	#endif
#endif
#if defined( USE_ENVMAP ) && defined( RE_IndirectSpecular )
	#ifdef USE_ANISOTROPY
		radiance += getIBLAnisotropyRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
	#else
		radiance += getIBLRadiance( geometryViewDir, geometryNormal, material.roughness );
	#endif
	#ifdef USE_CLEARCOAT
		clearcoatRadiance += getIBLRadiance( geometryViewDir, geometryClearcoatNormal, material.clearcoatRoughness );
	#endif
#endif`,zQ=`#if defined( RE_IndirectDiffuse )
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,kQ=`#if defined( USE_LOGDEPTHBUF )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,AQ=`#if defined( USE_LOGDEPTHBUF )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,wQ=`#ifdef USE_LOGDEPTHBUF
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,LQ=`#ifdef USE_LOGDEPTHBUF
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,_Q=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,CQ=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,PQ=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
	#if defined( USE_POINTS_UV )
		vec2 uv = vUv;
	#else
		vec2 uv = ( uvTransform * vec3( gl_PointCoord.x, 1.0 - gl_PointCoord.y, 1 ) ).xy;
	#endif
#endif
#ifdef USE_MAP
	diffuseColor *= texture2D( map, uv );
#endif
#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, uv ).g;
#endif`,TQ=`#if defined( USE_POINTS_UV )
	varying vec2 vUv;
#else
	#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
		uniform mat3 uvTransform;
	#endif
#endif
#ifdef USE_MAP
	uniform sampler2D map;
#endif
#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,IQ=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,SQ=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,yQ=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,vQ=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,jQ=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,fQ=`#ifdef USE_MORPHTARGETS
	#ifndef USE_INSTANCING_MORPH
		uniform float morphTargetBaseInfluence;
		uniform float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	#endif
	uniform sampler2DArray morphTargetsTexture;
	uniform ivec2 morphTargetsTextureSize;
	vec4 getMorph( const in int vertexIndex, const in int morphTargetIndex, const in int offset ) {
		int texelIndex = vertexIndex * MORPHTARGETS_TEXTURE_STRIDE + offset;
		int y = texelIndex / morphTargetsTextureSize.x;
		int x = texelIndex - y * morphTargetsTextureSize.x;
		ivec3 morphUV = ivec3( x, y, morphTargetIndex );
		return texelFetch( morphTargetsTexture, morphUV, 0 );
	}
#endif`,hQ=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,bQ=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
#ifdef FLAT_SHADED
	vec3 fdx = dFdx( vViewPosition );
	vec3 fdy = dFdy( vViewPosition );
	vec3 normal = normalize( cross( fdx, fdy ) );
#else
	vec3 normal = normalize( vNormal );
	#ifdef DOUBLE_SIDED
		normal *= faceDirection;
	#endif
#endif
#if defined( USE_NORMALMAP_TANGENTSPACE ) || defined( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY )
	#ifdef USE_TANGENT
		mat3 tbn = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn = getTangentFrame( - vViewPosition, normal,
		#if defined( USE_NORMALMAP )
			vNormalMapUv
		#elif defined( USE_CLEARCOAT_NORMALMAP )
			vClearcoatNormalMapUv
		#else
			vUv
		#endif
		);
	#endif
	#if defined( DOUBLE_SIDED ) && ! defined( FLAT_SHADED )
		tbn[0] *= faceDirection;
		tbn[1] *= faceDirection;
	#endif
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	#ifdef USE_TANGENT
		mat3 tbn2 = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn2 = getTangentFrame( - vViewPosition, normal, vClearcoatNormalMapUv );
	#endif
	#if defined( DOUBLE_SIDED ) && ! defined( FLAT_SHADED )
		tbn2[0] *= faceDirection;
		tbn2[1] *= faceDirection;
	#endif
#endif
vec3 nonPerturbedNormal = normal;`,xQ=`#ifdef USE_NORMALMAP_OBJECTSPACE
	normal = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#ifdef FLIP_SIDED
		normal = - normal;
	#endif
	#ifdef DOUBLE_SIDED
		normal = normal * faceDirection;
	#endif
	normal = normalize( normalMatrix * normal );
#elif defined( USE_NORMALMAP_TANGENTSPACE )
	vec3 mapN = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	mapN.xy *= normalScale;
	normal = normalize( tbn * mapN );
#elif defined( USE_BUMPMAP )
	normal = perturbNormalArb( - vViewPosition, normal, dHdxy_fwd(), faceDirection );
#endif`,pQ=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,gQ=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,mQ=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
	#endif
#endif`,uQ=`#ifdef USE_NORMALMAP
	uniform sampler2D normalMap;
	uniform vec2 normalScale;
#endif
#ifdef USE_NORMALMAP_OBJECTSPACE
	uniform mat3 normalMatrix;
#endif
#if ! defined ( USE_TANGENT ) && ( defined ( USE_NORMALMAP_TANGENTSPACE ) || defined ( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY ) )
	mat3 getTangentFrame( vec3 eye_pos, vec3 surf_norm, vec2 uv ) {
		vec3 q0 = dFdx( eye_pos.xyz );
		vec3 q1 = dFdy( eye_pos.xyz );
		vec2 st0 = dFdx( uv.st );
		vec2 st1 = dFdy( uv.st );
		vec3 N = surf_norm;
		vec3 q1perp = cross( q1, N );
		vec3 q0perp = cross( N, q0 );
		vec3 T = q1perp * st0.x + q0perp * st1.x;
		vec3 B = q1perp * st0.y + q0perp * st1.y;
		float det = max( dot( T, T ), dot( B, B ) );
		float scale = ( det == 0.0 ) ? 0.0 : inversesqrt( det );
		return mat3( T * scale, B * scale, N );
	}
#endif`,lQ=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,dQ=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,cQ=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,nQ=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,sQ=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,iQ=`vec3 packNormalToRGB( const in vec3 normal ) {
	return normalize( normal ) * 0.5 + 0.5;
}
vec3 unpackRGBToNormal( const in vec3 rgb ) {
	return 2.0 * rgb.xyz - 1.0;
}
const float PackUpscale = 256. / 255.;const float UnpackDownscale = 255. / 256.;const float ShiftRight8 = 1. / 256.;
const float Inv255 = 1. / 255.;
const vec4 PackFactors = vec4( 1.0, 256.0, 256.0 * 256.0, 256.0 * 256.0 * 256.0 );
const vec2 UnpackFactors2 = vec2( UnpackDownscale, 1.0 / PackFactors.g );
const vec3 UnpackFactors3 = vec3( UnpackDownscale / PackFactors.rg, 1.0 / PackFactors.b );
const vec4 UnpackFactors4 = vec4( UnpackDownscale / PackFactors.rgb, 1.0 / PackFactors.a );
vec4 packDepthToRGBA( const in float v ) {
	if( v <= 0.0 )
		return vec4( 0., 0., 0., 0. );
	if( v >= 1.0 )
		return vec4( 1., 1., 1., 1. );
	float vuf;
	float af = modf( v * PackFactors.a, vuf );
	float bf = modf( vuf * ShiftRight8, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec4( vuf * Inv255, gf * PackUpscale, bf * PackUpscale, af );
}
vec3 packDepthToRGB( const in float v ) {
	if( v <= 0.0 )
		return vec3( 0., 0., 0. );
	if( v >= 1.0 )
		return vec3( 1., 1., 1. );
	float vuf;
	float bf = modf( v * PackFactors.b, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec3( vuf * Inv255, gf * PackUpscale, bf );
}
vec2 packDepthToRG( const in float v ) {
	if( v <= 0.0 )
		return vec2( 0., 0. );
	if( v >= 1.0 )
		return vec2( 1., 1. );
	float vuf;
	float gf = modf( v * 256., vuf );
	return vec2( vuf * Inv255, gf );
}
float unpackRGBAToDepth( const in vec4 v ) {
	return dot( v, UnpackFactors4 );
}
float unpackRGBToDepth( const in vec3 v ) {
	return dot( v, UnpackFactors3 );
}
float unpackRGToDepth( const in vec2 v ) {
	return v.r * UnpackFactors2.r + v.g * UnpackFactors2.g;
}
vec4 pack2HalfToRGBA( const in vec2 v ) {
	vec4 r = vec4( v.x, fract( v.x * 255.0 ), v.y, fract( v.y * 255.0 ) );
	return vec4( r.x - r.y / 255.0, r.y, r.z - r.w / 255.0, r.w );
}
vec2 unpackRGBATo2Half( const in vec4 v ) {
	return vec2( v.x + ( v.y / 255.0 ), v.z + ( v.w / 255.0 ) );
}
float viewZToOrthographicDepth( const in float viewZ, const in float near, const in float far ) {
	return ( viewZ + near ) / ( near - far );
}
float orthographicDepthToViewZ( const in float depth, const in float near, const in float far ) {
	return depth * ( near - far ) - near;
}
float viewZToPerspectiveDepth( const in float viewZ, const in float near, const in float far ) {
	return ( ( near + viewZ ) * far ) / ( ( far - near ) * viewZ );
}
float perspectiveDepthToViewZ( const in float depth, const in float near, const in float far ) {
	return ( near * far ) / ( ( far - near ) * depth - far );
}`,oQ=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,aQ=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,rQ=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,tQ=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,eQ=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,JZ=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,$Z=`#if NUM_SPOT_LIGHT_COORDS > 0
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#if NUM_SPOT_LIGHT_MAPS > 0
	uniform sampler2D spotLightMap[ NUM_SPOT_LIGHT_MAPS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform sampler2D directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		uniform sampler2D spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform sampler2D pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
	float texture2DCompare( sampler2D depths, vec2 uv, float compare ) {
		return step( compare, unpackRGBAToDepth( texture2D( depths, uv ) ) );
	}
	vec2 texture2DDistribution( sampler2D shadow, vec2 uv ) {
		return unpackRGBATo2Half( texture2D( shadow, uv ) );
	}
	float VSMShadow (sampler2D shadow, vec2 uv, float compare ){
		float occlusion = 1.0;
		vec2 distribution = texture2DDistribution( shadow, uv );
		float hard_shadow = step( compare , distribution.x );
		if (hard_shadow != 1.0 ) {
			float distance = compare - distribution.x ;
			float variance = max( 0.00000, distribution.y * distribution.y );
			float softness_probability = variance / (variance + distance * distance );			softness_probability = clamp( ( softness_probability - 0.3 ) / ( 0.95 - 0.3 ), 0.0, 1.0 );			occlusion = clamp( max( hard_shadow, softness_probability ), 0.0, 1.0 );
		}
		return occlusion;
	}
	float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
		float shadow = 1.0;
		shadowCoord.xyz /= shadowCoord.w;
		shadowCoord.z += shadowBias;
		bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
		bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
		if ( frustumTest ) {
		#if defined( SHADOWMAP_TYPE_PCF )
			vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
			float dx0 = - texelSize.x * shadowRadius;
			float dy0 = - texelSize.y * shadowRadius;
			float dx1 = + texelSize.x * shadowRadius;
			float dy1 = + texelSize.y * shadowRadius;
			float dx2 = dx0 / 2.0;
			float dy2 = dy0 / 2.0;
			float dx3 = dx1 / 2.0;
			float dy3 = dy1 / 2.0;
			shadow = (
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy, shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, dy1 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy1 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, dy1 ), shadowCoord.z )
			) * ( 1.0 / 17.0 );
		#elif defined( SHADOWMAP_TYPE_PCF_SOFT )
			vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
			float dx = texelSize.x;
			float dy = texelSize.y;
			vec2 uv = shadowCoord.xy;
			vec2 f = fract( uv * shadowMapSize + 0.5 );
			uv -= f * texelSize;
			shadow = (
				texture2DCompare( shadowMap, uv, shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + vec2( dx, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + vec2( 0.0, dy ), shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + texelSize, shadowCoord.z ) +
				mix( texture2DCompare( shadowMap, uv + vec2( -dx, 0.0 ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, 0.0 ), shadowCoord.z ),
					 f.x ) +
				mix( texture2DCompare( shadowMap, uv + vec2( -dx, dy ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, dy ), shadowCoord.z ),
					 f.x ) +
				mix( texture2DCompare( shadowMap, uv + vec2( 0.0, -dy ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( 0.0, 2.0 * dy ), shadowCoord.z ),
					 f.y ) +
				mix( texture2DCompare( shadowMap, uv + vec2( dx, -dy ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( dx, 2.0 * dy ), shadowCoord.z ),
					 f.y ) +
				mix( mix( texture2DCompare( shadowMap, uv + vec2( -dx, -dy ), shadowCoord.z ),
						  texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, -dy ), shadowCoord.z ),
						  f.x ),
					 mix( texture2DCompare( shadowMap, uv + vec2( -dx, 2.0 * dy ), shadowCoord.z ),
						  texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, 2.0 * dy ), shadowCoord.z ),
						  f.x ),
					 f.y )
			) * ( 1.0 / 9.0 );
		#elif defined( SHADOWMAP_TYPE_VSM )
			shadow = VSMShadow( shadowMap, shadowCoord.xy, shadowCoord.z );
		#else
			shadow = texture2DCompare( shadowMap, shadowCoord.xy, shadowCoord.z );
		#endif
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	vec2 cubeToUV( vec3 v, float texelSizeY ) {
		vec3 absV = abs( v );
		float scaleToCube = 1.0 / max( absV.x, max( absV.y, absV.z ) );
		absV *= scaleToCube;
		v *= scaleToCube * ( 1.0 - 2.0 * texelSizeY );
		vec2 planar = v.xy;
		float almostATexel = 1.5 * texelSizeY;
		float almostOne = 1.0 - almostATexel;
		if ( absV.z >= almostOne ) {
			if ( v.z > 0.0 )
				planar.x = 4.0 - v.x;
		} else if ( absV.x >= almostOne ) {
			float signX = sign( v.x );
			planar.x = v.z * signX + 2.0 * signX;
		} else if ( absV.y >= almostOne ) {
			float signY = sign( v.y );
			planar.x = v.x + 2.0 * signY + 2.0;
			planar.y = v.z * signY - 2.0;
		}
		return vec2( 0.125, 0.25 ) * planar + vec2( 0.375, 0.75 );
	}
	float getPointShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		
		float lightToPositionLength = length( lightToPosition );
		if ( lightToPositionLength - shadowCameraFar <= 0.0 && lightToPositionLength - shadowCameraNear >= 0.0 ) {
			float dp = ( lightToPositionLength - shadowCameraNear ) / ( shadowCameraFar - shadowCameraNear );			dp += shadowBias;
			vec3 bd3D = normalize( lightToPosition );
			vec2 texelSize = vec2( 1.0 ) / ( shadowMapSize * vec2( 4.0, 2.0 ) );
			#if defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_PCF_SOFT ) || defined( SHADOWMAP_TYPE_VSM )
				vec2 offset = vec2( - 1, 1 ) * shadowRadius * texelSize.y;
				shadow = (
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xyy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yyy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xyx, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yyx, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xxy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yxy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xxx, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yxx, texelSize.y ), dp )
				) * ( 1.0 / 9.0 );
			#else
				shadow = texture2DCompare( shadowMap, cubeToUV( bd3D, texelSize.y ), dp );
			#endif
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
#endif`,QZ=`#if NUM_SPOT_LIGHT_COORDS > 0
	uniform mat4 spotLightMatrix[ NUM_SPOT_LIGHT_COORDS ];
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform mat4 directionalShadowMatrix[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform mat4 pointShadowMatrix[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
#endif`,ZZ=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
	vec3 shadowWorldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
	vec4 shadowWorldPosition;
#endif
#if defined( USE_SHADOWMAP )
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * directionalLightShadows[ i ].shadowNormalBias, 0 );
			vDirectionalShadowCoord[ i ] = directionalShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * pointLightShadows[ i ].shadowNormalBias, 0 );
			vPointShadowCoord[ i ] = pointShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
#endif
#if NUM_SPOT_LIGHT_COORDS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_COORDS; i ++ ) {
		shadowWorldPosition = worldPosition;
		#if ( defined( USE_SHADOWMAP ) && UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
			shadowWorldPosition.xyz += shadowWorldNormal * spotLightShadows[ i ].shadowNormalBias;
		#endif
		vSpotLightCoord[ i ] = spotLightMatrix[ i ] * shadowWorldPosition;
	}
	#pragma unroll_loop_end
#endif`,WZ=`float getShadowMask() {
	float shadow = 1.0;
	#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
		directionalLight = directionalLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( directionalShadowMap[ i ], directionalLight.shadowMapSize, directionalLight.shadowIntensity, directionalLight.shadowBias, directionalLight.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_SHADOWS; i ++ ) {
		spotLight = spotLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( spotShadowMap[ i ], spotLight.shadowMapSize, spotLight.shadowIntensity, spotLight.shadowBias, spotLight.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
		pointLight = pointLightShadows[ i ];
		shadow *= receiveShadow ? getPointShadow( pointShadowMap[ i ], pointLight.shadowMapSize, pointLight.shadowIntensity, pointLight.shadowBias, pointLight.shadowRadius, vPointShadowCoord[ i ], pointLight.shadowCameraNear, pointLight.shadowCameraFar ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#endif
	return shadow;
}`,YZ=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,HZ=`#ifdef USE_SKINNING
	uniform mat4 bindMatrix;
	uniform mat4 bindMatrixInverse;
	uniform highp sampler2D boneTexture;
	mat4 getBoneMatrix( const in float i ) {
		int size = textureSize( boneTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( boneTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( boneTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( boneTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( boneTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
#endif`,XZ=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,KZ=`#ifdef USE_SKINNING
	mat4 skinMatrix = mat4( 0.0 );
	skinMatrix += skinWeight.x * boneMatX;
	skinMatrix += skinWeight.y * boneMatY;
	skinMatrix += skinWeight.z * boneMatZ;
	skinMatrix += skinWeight.w * boneMatW;
	skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;
	objectNormal = vec4( skinMatrix * vec4( objectNormal, 0.0 ) ).xyz;
	#ifdef USE_TANGENT
		objectTangent = vec4( skinMatrix * vec4( objectTangent, 0.0 ) ).xyz;
	#endif
#endif`,GZ=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,UZ=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,qZ=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,EZ=`#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
uniform float toneMappingExposure;
vec3 LinearToneMapping( vec3 color ) {
	return saturate( toneMappingExposure * color );
}
vec3 ReinhardToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	return saturate( color / ( vec3( 1.0 ) + color ) );
}
vec3 CineonToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	color = max( vec3( 0.0 ), color - 0.004 );
	return pow( ( color * ( 6.2 * color + 0.5 ) ) / ( color * ( 6.2 * color + 1.7 ) + 0.06 ), vec3( 2.2 ) );
}
vec3 RRTAndODTFit( vec3 v ) {
	vec3 a = v * ( v + 0.0245786 ) - 0.000090537;
	vec3 b = v * ( 0.983729 * v + 0.4329510 ) + 0.238081;
	return a / b;
}
vec3 ACESFilmicToneMapping( vec3 color ) {
	const mat3 ACESInputMat = mat3(
		vec3( 0.59719, 0.07600, 0.02840 ),		vec3( 0.35458, 0.90834, 0.13383 ),
		vec3( 0.04823, 0.01566, 0.83777 )
	);
	const mat3 ACESOutputMat = mat3(
		vec3(  1.60475, -0.10208, -0.00327 ),		vec3( -0.53108,  1.10813, -0.07276 ),
		vec3( -0.07367, -0.00605,  1.07602 )
	);
	color *= toneMappingExposure / 0.6;
	color = ACESInputMat * color;
	color = RRTAndODTFit( color );
	color = ACESOutputMat * color;
	return saturate( color );
}
const mat3 LINEAR_REC2020_TO_LINEAR_SRGB = mat3(
	vec3( 1.6605, - 0.1246, - 0.0182 ),
	vec3( - 0.5876, 1.1329, - 0.1006 ),
	vec3( - 0.0728, - 0.0083, 1.1187 )
);
const mat3 LINEAR_SRGB_TO_LINEAR_REC2020 = mat3(
	vec3( 0.6274, 0.0691, 0.0164 ),
	vec3( 0.3293, 0.9195, 0.0880 ),
	vec3( 0.0433, 0.0113, 0.8956 )
);
vec3 agxDefaultContrastApprox( vec3 x ) {
	vec3 x2 = x * x;
	vec3 x4 = x2 * x2;
	return + 15.5 * x4 * x2
		- 40.14 * x4 * x
		+ 31.96 * x4
		- 6.868 * x2 * x
		+ 0.4298 * x2
		+ 0.1191 * x
		- 0.00232;
}
vec3 AgXToneMapping( vec3 color ) {
	const mat3 AgXInsetMatrix = mat3(
		vec3( 0.856627153315983, 0.137318972929847, 0.11189821299995 ),
		vec3( 0.0951212405381588, 0.761241990602591, 0.0767994186031903 ),
		vec3( 0.0482516061458583, 0.101439036467562, 0.811302368396859 )
	);
	const mat3 AgXOutsetMatrix = mat3(
		vec3( 1.1271005818144368, - 0.1413297634984383, - 0.14132976349843826 ),
		vec3( - 0.11060664309660323, 1.157823702216272, - 0.11060664309660294 ),
		vec3( - 0.016493938717834573, - 0.016493938717834257, 1.2519364065950405 )
	);
	const float AgxMinEv = - 12.47393;	const float AgxMaxEv = 4.026069;
	color *= toneMappingExposure;
	color = LINEAR_SRGB_TO_LINEAR_REC2020 * color;
	color = AgXInsetMatrix * color;
	color = max( color, 1e-10 );	color = log2( color );
	color = ( color - AgxMinEv ) / ( AgxMaxEv - AgxMinEv );
	color = clamp( color, 0.0, 1.0 );
	color = agxDefaultContrastApprox( color );
	color = AgXOutsetMatrix * color;
	color = pow( max( vec3( 0.0 ), color ), vec3( 2.2 ) );
	color = LINEAR_REC2020_TO_LINEAR_SRGB * color;
	color = clamp( color, 0.0, 1.0 );
	return color;
}
vec3 NeutralToneMapping( vec3 color ) {
	const float StartCompression = 0.8 - 0.04;
	const float Desaturation = 0.15;
	color *= toneMappingExposure;
	float x = min( color.r, min( color.g, color.b ) );
	float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
	color -= offset;
	float peak = max( color.r, max( color.g, color.b ) );
	if ( peak < StartCompression ) return color;
	float d = 1. - StartCompression;
	float newPeak = 1. - d * d / ( peak + d - StartCompression );
	color *= newPeak / peak;
	float g = 1. - 1. / ( Desaturation * ( peak - newPeak ) + 1. );
	return mix( color, vec3( newPeak ), g );
}
vec3 CustomToneMapping( vec3 color ) { return color; }`,VZ=`#ifdef USE_TRANSMISSION
	material.transmission = transmission;
	material.transmissionAlpha = 1.0;
	material.thickness = thickness;
	material.attenuationDistance = attenuationDistance;
	material.attenuationColor = attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		material.transmission *= texture2D( transmissionMap, vTransmissionMapUv ).r;
	#endif
	#ifdef USE_THICKNESSMAP
		material.thickness *= texture2D( thicknessMap, vThicknessMapUv ).g;
	#endif
	vec3 pos = vWorldPosition;
	vec3 v = normalize( cameraPosition - pos );
	vec3 n = inverseTransformDirection( normal, viewMatrix );
	vec4 transmitted = getIBLVolumeRefraction(
		n, v, material.roughness, material.diffuseColor, material.specularColor, material.specularF90,
		pos, modelMatrix, viewMatrix, projectionMatrix, material.dispersion, material.ior, material.thickness,
		material.attenuationColor, material.attenuationDistance );
	material.transmissionAlpha = mix( material.transmissionAlpha, transmitted.a, material.transmission );
	totalDiffuse = mix( totalDiffuse, transmitted.rgb, material.transmission );
#endif`,FZ=`#ifdef USE_TRANSMISSION
	uniform float transmission;
	uniform float thickness;
	uniform float attenuationDistance;
	uniform vec3 attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		uniform sampler2D transmissionMap;
	#endif
	#ifdef USE_THICKNESSMAP
		uniform sampler2D thicknessMap;
	#endif
	uniform vec2 transmissionSamplerSize;
	uniform sampler2D transmissionSamplerMap;
	uniform mat4 modelMatrix;
	uniform mat4 projectionMatrix;
	varying vec3 vWorldPosition;
	float w0( float a ) {
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - a + 3.0 ) - 3.0 ) + 1.0 );
	}
	float w1( float a ) {
		return ( 1.0 / 6.0 ) * ( a *  a * ( 3.0 * a - 6.0 ) + 4.0 );
	}
	float w2( float a ){
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - 3.0 * a + 3.0 ) + 3.0 ) + 1.0 );
	}
	float w3( float a ) {
		return ( 1.0 / 6.0 ) * ( a * a * a );
	}
	float g0( float a ) {
		return w0( a ) + w1( a );
	}
	float g1( float a ) {
		return w2( a ) + w3( a );
	}
	float h0( float a ) {
		return - 1.0 + w1( a ) / ( w0( a ) + w1( a ) );
	}
	float h1( float a ) {
		return 1.0 + w3( a ) / ( w2( a ) + w3( a ) );
	}
	vec4 bicubic( sampler2D tex, vec2 uv, vec4 texelSize, float lod ) {
		uv = uv * texelSize.zw + 0.5;
		vec2 iuv = floor( uv );
		vec2 fuv = fract( uv );
		float g0x = g0( fuv.x );
		float g1x = g1( fuv.x );
		float h0x = h0( fuv.x );
		float h1x = h1( fuv.x );
		float h0y = h0( fuv.y );
		float h1y = h1( fuv.y );
		vec2 p0 = ( vec2( iuv.x + h0x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p1 = ( vec2( iuv.x + h1x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p2 = ( vec2( iuv.x + h0x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		vec2 p3 = ( vec2( iuv.x + h1x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		return g0( fuv.y ) * ( g0x * textureLod( tex, p0, lod ) + g1x * textureLod( tex, p1, lod ) ) +
			g1( fuv.y ) * ( g0x * textureLod( tex, p2, lod ) + g1x * textureLod( tex, p3, lod ) );
	}
	vec4 textureBicubic( sampler2D sampler, vec2 uv, float lod ) {
		vec2 fLodSize = vec2( textureSize( sampler, int( lod ) ) );
		vec2 cLodSize = vec2( textureSize( sampler, int( lod + 1.0 ) ) );
		vec2 fLodSizeInv = 1.0 / fLodSize;
		vec2 cLodSizeInv = 1.0 / cLodSize;
		vec4 fSample = bicubic( sampler, uv, vec4( fLodSizeInv, fLodSize ), floor( lod ) );
		vec4 cSample = bicubic( sampler, uv, vec4( cLodSizeInv, cLodSize ), ceil( lod ) );
		return mix( fSample, cSample, fract( lod ) );
	}
	vec3 getVolumeTransmissionRay( const in vec3 n, const in vec3 v, const in float thickness, const in float ior, const in mat4 modelMatrix ) {
		vec3 refractionVector = refract( - v, normalize( n ), 1.0 / ior );
		vec3 modelScale;
		modelScale.x = length( vec3( modelMatrix[ 0 ].xyz ) );
		modelScale.y = length( vec3( modelMatrix[ 1 ].xyz ) );
		modelScale.z = length( vec3( modelMatrix[ 2 ].xyz ) );
		return normalize( refractionVector ) * thickness * modelScale;
	}
	float applyIorToRoughness( const in float roughness, const in float ior ) {
		return roughness * clamp( ior * 2.0 - 2.0, 0.0, 1.0 );
	}
	vec4 getTransmissionSample( const in vec2 fragCoord, const in float roughness, const in float ior ) {
		float lod = log2( transmissionSamplerSize.x ) * applyIorToRoughness( roughness, ior );
		return textureBicubic( transmissionSamplerMap, fragCoord.xy, lod );
	}
	vec3 volumeAttenuation( const in float transmissionDistance, const in vec3 attenuationColor, const in float attenuationDistance ) {
		if ( isinf( attenuationDistance ) ) {
			return vec3( 1.0 );
		} else {
			vec3 attenuationCoefficient = -log( attenuationColor ) / attenuationDistance;
			vec3 transmittance = exp( - attenuationCoefficient * transmissionDistance );			return transmittance;
		}
	}
	vec4 getIBLVolumeRefraction( const in vec3 n, const in vec3 v, const in float roughness, const in vec3 diffuseColor,
		const in vec3 specularColor, const in float specularF90, const in vec3 position, const in mat4 modelMatrix,
		const in mat4 viewMatrix, const in mat4 projMatrix, const in float dispersion, const in float ior, const in float thickness,
		const in vec3 attenuationColor, const in float attenuationDistance ) {
		vec4 transmittedLight;
		vec3 transmittance;
		#ifdef USE_DISPERSION
			float halfSpread = ( ior - 1.0 ) * 0.025 * dispersion;
			vec3 iors = vec3( ior - halfSpread, ior, ior + halfSpread );
			for ( int i = 0; i < 3; i ++ ) {
				vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, iors[ i ], modelMatrix );
				vec3 refractedRayExit = position + transmissionRay;
		
				vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
				vec2 refractionCoords = ndcPos.xy / ndcPos.w;
				refractionCoords += 1.0;
				refractionCoords /= 2.0;
		
				vec4 transmissionSample = getTransmissionSample( refractionCoords, roughness, iors[ i ] );
				transmittedLight[ i ] = transmissionSample[ i ];
				transmittedLight.a += transmissionSample.a;
				transmittance[ i ] = diffuseColor[ i ] * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance )[ i ];
			}
			transmittedLight.a /= 3.0;
		
		#else
		
			vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, ior, modelMatrix );
			vec3 refractedRayExit = position + transmissionRay;
			vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
			vec2 refractionCoords = ndcPos.xy / ndcPos.w;
			refractionCoords += 1.0;
			refractionCoords /= 2.0;
			transmittedLight = getTransmissionSample( refractionCoords, roughness, ior );
			transmittance = diffuseColor * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance );
		
		#endif
		vec3 attenuatedColor = transmittance * transmittedLight.rgb;
		vec3 F = EnvironmentBRDF( n, v, specularColor, specularF90, roughness );
		float transmittanceFactor = ( transmittance.r + transmittance.g + transmittance.b ) / 3.0;
		return vec4( ( 1.0 - F ) * attenuatedColor, 1.0 - ( 1.0 - transmittedLight.a ) * transmittanceFactor );
	}
#endif`,DZ=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_SPECULARMAP
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,RZ=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	uniform mat3 mapTransform;
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	uniform mat3 alphaMapTransform;
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	uniform mat3 lightMapTransform;
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	uniform mat3 aoMapTransform;
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	uniform mat3 bumpMapTransform;
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	uniform mat3 normalMapTransform;
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_DISPLACEMENTMAP
	uniform mat3 displacementMapTransform;
	varying vec2 vDisplacementMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	uniform mat3 emissiveMapTransform;
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	uniform mat3 metalnessMapTransform;
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	uniform mat3 roughnessMapTransform;
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	uniform mat3 anisotropyMapTransform;
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	uniform mat3 clearcoatMapTransform;
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform mat3 clearcoatNormalMapTransform;
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform mat3 clearcoatRoughnessMapTransform;
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	uniform mat3 sheenColorMapTransform;
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	uniform mat3 sheenRoughnessMapTransform;
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	uniform mat3 iridescenceMapTransform;
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform mat3 iridescenceThicknessMapTransform;
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SPECULARMAP
	uniform mat3 specularMapTransform;
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	uniform mat3 specularColorMapTransform;
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	uniform mat3 specularIntensityMapTransform;
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,NZ=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	vUv = vec3( uv, 1 ).xy;
#endif
#ifdef USE_MAP
	vMapUv = ( mapTransform * vec3( MAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ALPHAMAP
	vAlphaMapUv = ( alphaMapTransform * vec3( ALPHAMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_LIGHTMAP
	vLightMapUv = ( lightMapTransform * vec3( LIGHTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_AOMAP
	vAoMapUv = ( aoMapTransform * vec3( AOMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_BUMPMAP
	vBumpMapUv = ( bumpMapTransform * vec3( BUMPMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_NORMALMAP
	vNormalMapUv = ( normalMapTransform * vec3( NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_DISPLACEMENTMAP
	vDisplacementMapUv = ( displacementMapTransform * vec3( DISPLACEMENTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_EMISSIVEMAP
	vEmissiveMapUv = ( emissiveMapTransform * vec3( EMISSIVEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_METALNESSMAP
	vMetalnessMapUv = ( metalnessMapTransform * vec3( METALNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ROUGHNESSMAP
	vRoughnessMapUv = ( roughnessMapTransform * vec3( ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ANISOTROPYMAP
	vAnisotropyMapUv = ( anisotropyMapTransform * vec3( ANISOTROPYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOATMAP
	vClearcoatMapUv = ( clearcoatMapTransform * vec3( CLEARCOATMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	vClearcoatNormalMapUv = ( clearcoatNormalMapTransform * vec3( CLEARCOAT_NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	vClearcoatRoughnessMapUv = ( clearcoatRoughnessMapTransform * vec3( CLEARCOAT_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCEMAP
	vIridescenceMapUv = ( iridescenceMapTransform * vec3( IRIDESCENCEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	vIridescenceThicknessMapUv = ( iridescenceThicknessMapTransform * vec3( IRIDESCENCE_THICKNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_COLORMAP
	vSheenColorMapUv = ( sheenColorMapTransform * vec3( SHEEN_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	vSheenRoughnessMapUv = ( sheenRoughnessMapTransform * vec3( SHEEN_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULARMAP
	vSpecularMapUv = ( specularMapTransform * vec3( SPECULARMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_COLORMAP
	vSpecularColorMapUv = ( specularColorMapTransform * vec3( SPECULAR_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	vSpecularIntensityMapUv = ( specularIntensityMapTransform * vec3( SPECULAR_INTENSITYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_TRANSMISSIONMAP
	vTransmissionMapUv = ( transmissionMapTransform * vec3( TRANSMISSIONMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_THICKNESSMAP
	vThicknessMapUv = ( thicknessMapTransform * vec3( THICKNESSMAP_UV, 1 ) ).xy;
#endif`,OZ=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`,MZ=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,BZ=`uniform sampler2D t2D;
uniform float backgroundIntensity;
varying vec2 vUv;
void main() {
	vec4 texColor = texture2D( t2D, vUv );
	#ifdef DECODE_VIDEO_TEXTURE
		texColor = vec4( mix( pow( texColor.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), texColor.rgb * 0.0773993808, vec3( lessThanEqual( texColor.rgb, vec3( 0.04045 ) ) ) ), texColor.w );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,zZ=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,kZ=`#ifdef ENVMAP_TYPE_CUBE
	uniform samplerCube envMap;
#elif defined( ENVMAP_TYPE_CUBE_UV )
	uniform sampler2D envMap;
#endif
uniform float flipEnvMap;
uniform float backgroundBlurriness;
uniform float backgroundIntensity;
uniform mat3 backgroundRotation;
varying vec3 vWorldDirection;
#include <cube_uv_reflection_fragment>
void main() {
	#ifdef ENVMAP_TYPE_CUBE
		vec4 texColor = textureCube( envMap, backgroundRotation * vec3( flipEnvMap * vWorldDirection.x, vWorldDirection.yz ) );
	#elif defined( ENVMAP_TYPE_CUBE_UV )
		vec4 texColor = textureCubeUV( envMap, backgroundRotation * vWorldDirection, backgroundBlurriness );
	#else
		vec4 texColor = vec4( 0.0, 0.0, 0.0, 1.0 );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,AZ=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,wZ=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,LZ=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
varying vec2 vHighPrecisionZW;
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vHighPrecisionZW = gl_Position.zw;
}`,_Z=`#if DEPTH_PACKING == 3200
	uniform float opacity;
#endif
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
varying vec2 vHighPrecisionZW;
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#if DEPTH_PACKING == 3200
		diffuseColor.a = opacity;
	#endif
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <logdepthbuf_fragment>
	float fragCoordZ = 0.5 * vHighPrecisionZW[0] / vHighPrecisionZW[1] + 0.5;
	#if DEPTH_PACKING == 3200
		gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );
	#elif DEPTH_PACKING == 3201
		gl_FragColor = packDepthToRGBA( fragCoordZ );
	#elif DEPTH_PACKING == 3202
		gl_FragColor = vec4( packDepthToRGB( fragCoordZ ), 1.0 );
	#elif DEPTH_PACKING == 3203
		gl_FragColor = vec4( packDepthToRG( fragCoordZ ), 0.0, 1.0 );
	#endif
}`,CZ=`#define DISTANCE
varying vec3 vWorldPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <worldpos_vertex>
	#include <clipping_planes_vertex>
	vWorldPosition = worldPosition.xyz;
}`,PZ=`#define DISTANCE
uniform vec3 referencePosition;
uniform float nearDistance;
uniform float farDistance;
varying vec3 vWorldPosition;
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <clipping_planes_pars_fragment>
void main () {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	float dist = length( vWorldPosition - referencePosition );
	dist = ( dist - nearDistance ) / ( farDistance - nearDistance );
	dist = saturate( dist );
	gl_FragColor = packDepthToRGBA( dist );
}`,TZ=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,IZ=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,SZ=`uniform float scale;
attribute float lineDistance;
varying float vLineDistance;
#include <common>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	vLineDistance = scale * lineDistance;
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,yZ=`uniform vec3 diffuse;
uniform float opacity;
uniform float dashSize;
uniform float totalSize;
varying float vLineDistance;
#include <common>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	if ( mod( vLineDistance, totalSize ) > dashSize ) {
		discard;
	}
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,vZ=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#if defined ( USE_ENVMAP ) || defined ( USE_SKINNING )
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinbase_vertex>
		#include <skinnormal_vertex>
		#include <defaultnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <fog_vertex>
}`,jZ=`uniform vec3 diffuse;
uniform float opacity;
#ifndef FLAT_SHADED
	varying vec3 vNormal;
#endif
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		reflectedLight.indirectDiffuse += lightMapTexel.rgb * lightMapIntensity * RECIPROCAL_PI;
	#else
		reflectedLight.indirectDiffuse += vec3( 1.0 );
	#endif
	#include <aomap_fragment>
	reflectedLight.indirectDiffuse *= diffuseColor.rgb;
	vec3 outgoingLight = reflectedLight.indirectDiffuse;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,fZ=`#define LAMBERT
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,hZ=`#define LAMBERT
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_lambert_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_lambert_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,bZ=`#define MATCAP
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <displacementmap_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
	vViewPosition = - mvPosition.xyz;
}`,xZ=`#define MATCAP
uniform vec3 diffuse;
uniform float opacity;
uniform sampler2D matcap;
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	vec3 viewDir = normalize( vViewPosition );
	vec3 x = normalize( vec3( viewDir.z, 0.0, - viewDir.x ) );
	vec3 y = cross( viewDir, x );
	vec2 uv = vec2( dot( x, normal ), dot( y, normal ) ) * 0.495 + 0.5;
	#ifdef USE_MATCAP
		vec4 matcapColor = texture2D( matcap, uv );
	#else
		vec4 matcapColor = vec4( vec3( mix( 0.2, 0.8, uv.y ) ), 1.0 );
	#endif
	vec3 outgoingLight = diffuseColor.rgb * matcapColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,pZ=`#define NORMAL
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	vViewPosition = - mvPosition.xyz;
#endif
}`,gZ=`#define NORMAL
uniform float opacity;
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <packing>
#include <uv_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 0.0, 0.0, 0.0, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	gl_FragColor = vec4( packNormalToRGB( normal ), diffuseColor.a );
	#ifdef OPAQUE
		gl_FragColor.a = 1.0;
	#endif
}`,mZ=`#define PHONG
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,uZ=`#define PHONG
uniform vec3 diffuse;
uniform vec3 emissive;
uniform vec3 specular;
uniform float shininess;
uniform float opacity;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_phong_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_phong_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + reflectedLight.directSpecular + reflectedLight.indirectSpecular + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,lZ=`#define STANDARD
varying vec3 vViewPosition;
#ifdef USE_TRANSMISSION
	varying vec3 vWorldPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
#ifdef USE_TRANSMISSION
	vWorldPosition = worldPosition.xyz;
#endif
}`,dZ=`#define STANDARD
#ifdef PHYSICAL
	#define IOR
	#define USE_SPECULAR
#endif
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float roughness;
uniform float metalness;
uniform float opacity;
#ifdef IOR
	uniform float ior;
#endif
#ifdef USE_SPECULAR
	uniform float specularIntensity;
	uniform vec3 specularColor;
	#ifdef USE_SPECULAR_COLORMAP
		uniform sampler2D specularColorMap;
	#endif
	#ifdef USE_SPECULAR_INTENSITYMAP
		uniform sampler2D specularIntensityMap;
	#endif
#endif
#ifdef USE_CLEARCOAT
	uniform float clearcoat;
	uniform float clearcoatRoughness;
#endif
#ifdef USE_DISPERSION
	uniform float dispersion;
#endif
#ifdef USE_IRIDESCENCE
	uniform float iridescence;
	uniform float iridescenceIOR;
	uniform float iridescenceThicknessMinimum;
	uniform float iridescenceThicknessMaximum;
#endif
#ifdef USE_SHEEN
	uniform vec3 sheenColor;
	uniform float sheenRoughness;
	#ifdef USE_SHEEN_COLORMAP
		uniform sampler2D sheenColorMap;
	#endif
	#ifdef USE_SHEEN_ROUGHNESSMAP
		uniform sampler2D sheenRoughnessMap;
	#endif
#endif
#ifdef USE_ANISOTROPY
	uniform vec2 anisotropyVector;
	#ifdef USE_ANISOTROPYMAP
		uniform sampler2D anisotropyMap;
	#endif
#endif
varying vec3 vViewPosition;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <iridescence_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_physical_pars_fragment>
#include <transmission_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <clearcoat_pars_fragment>
#include <iridescence_pars_fragment>
#include <roughnessmap_pars_fragment>
#include <metalnessmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <roughnessmap_fragment>
	#include <metalnessmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <clearcoat_normal_fragment_begin>
	#include <clearcoat_normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_physical_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 totalDiffuse = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse;
	vec3 totalSpecular = reflectedLight.directSpecular + reflectedLight.indirectSpecular;
	#include <transmission_fragment>
	vec3 outgoingLight = totalDiffuse + totalSpecular + totalEmissiveRadiance;
	#ifdef USE_SHEEN
		float sheenEnergyComp = 1.0 - 0.157 * max3( material.sheenColor );
		outgoingLight = outgoingLight * sheenEnergyComp + sheenSpecularDirect + sheenSpecularIndirect;
	#endif
	#ifdef USE_CLEARCOAT
		float dotNVcc = saturate( dot( geometryClearcoatNormal, geometryViewDir ) );
		vec3 Fcc = F_Schlick( material.clearcoatF0, material.clearcoatF90, dotNVcc );
		outgoingLight = outgoingLight * ( 1.0 - material.clearcoat * Fcc ) + ( clearcoatSpecularDirect + clearcoatSpecularIndirect ) * material.clearcoat;
	#endif
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,cZ=`#define TOON
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,nZ=`#define TOON
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <gradientmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_toon_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_toon_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,sZ=`uniform float size;
uniform float scale;
#include <common>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
#ifdef USE_POINTS_UV
	varying vec2 vUv;
	uniform mat3 uvTransform;
#endif
void main() {
	#ifdef USE_POINTS_UV
		vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	#endif
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	gl_PointSize = size;
	#ifdef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) gl_PointSize *= ( scale / - mvPosition.z );
	#endif
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <fog_vertex>
}`,iZ=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <color_pars_fragment>
#include <map_particle_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_particle_fragment>
	#include <color_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,oZ=`#include <common>
#include <batching_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <shadowmap_pars_vertex>
void main() {
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,aZ=`uniform vec3 color;
uniform float opacity;
#include <common>
#include <packing>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <logdepthbuf_pars_fragment>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>
void main() {
	#include <logdepthbuf_fragment>
	gl_FragColor = vec4( color, opacity * ( 1.0 - getShadowMask() ) );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,rZ=`uniform float rotation;
uniform vec2 center;
#include <common>
#include <uv_pars_vertex>
#include <fog_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	vec4 mvPosition = modelViewMatrix[ 3 ];
	vec2 scale = vec2( length( modelMatrix[ 0 ].xyz ), length( modelMatrix[ 1 ].xyz ) );
	#ifndef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) scale *= - mvPosition.z;
	#endif
	vec2 alignedPosition = ( position.xy - ( center - vec2( 0.5 ) ) ) * scale;
	vec2 rotatedPosition;
	rotatedPosition.x = cos( rotation ) * alignedPosition.x - sin( rotation ) * alignedPosition.y;
	rotatedPosition.y = sin( rotation ) * alignedPosition.x + cos( rotation ) * alignedPosition.y;
	mvPosition.xy += rotatedPosition;
	gl_Position = projectionMatrix * mvPosition;
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,tZ=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,bJ={alphahash_fragment:B5,alphahash_pars_fragment:z5,alphamap_fragment:k5,alphamap_pars_fragment:A5,alphatest_fragment:w5,alphatest_pars_fragment:L5,aomap_fragment:_5,aomap_pars_fragment:C5,batching_pars_vertex:P5,batching_vertex:T5,begin_vertex:I5,beginnormal_vertex:S5,bsdfs:y5,iridescence_fragment:v5,bumpmap_pars_fragment:j5,clipping_planes_fragment:f5,clipping_planes_pars_fragment:h5,clipping_planes_pars_vertex:b5,clipping_planes_vertex:x5,color_fragment:p5,color_pars_fragment:g5,color_pars_vertex:m5,color_vertex:u5,common:l5,cube_uv_reflection_fragment:d5,defaultnormal_vertex:c5,displacementmap_pars_vertex:n5,displacementmap_vertex:s5,emissivemap_fragment:i5,emissivemap_pars_fragment:o5,colorspace_fragment:a5,colorspace_pars_fragment:r5,envmap_fragment:t5,envmap_common_pars_fragment:e5,envmap_pars_fragment:JQ,envmap_pars_vertex:$Q,envmap_physical_pars_fragment:EQ,envmap_vertex:QQ,fog_vertex:ZQ,fog_pars_vertex:WQ,fog_fragment:YQ,fog_pars_fragment:HQ,gradientmap_pars_fragment:XQ,lightmap_pars_fragment:KQ,lights_lambert_fragment:GQ,lights_lambert_pars_fragment:UQ,lights_pars_begin:qQ,lights_toon_fragment:VQ,lights_toon_pars_fragment:FQ,lights_phong_fragment:DQ,lights_phong_pars_fragment:RQ,lights_physical_fragment:NQ,lights_physical_pars_fragment:OQ,lights_fragment_begin:MQ,lights_fragment_maps:BQ,lights_fragment_end:zQ,logdepthbuf_fragment:kQ,logdepthbuf_pars_fragment:AQ,logdepthbuf_pars_vertex:wQ,logdepthbuf_vertex:LQ,map_fragment:_Q,map_pars_fragment:CQ,map_particle_fragment:PQ,map_particle_pars_fragment:TQ,metalnessmap_fragment:IQ,metalnessmap_pars_fragment:SQ,morphinstance_vertex:yQ,morphcolor_vertex:vQ,morphnormal_vertex:jQ,morphtarget_pars_vertex:fQ,morphtarget_vertex:hQ,normal_fragment_begin:bQ,normal_fragment_maps:xQ,normal_pars_fragment:pQ,normal_pars_vertex:gQ,normal_vertex:mQ,normalmap_pars_fragment:uQ,clearcoat_normal_fragment_begin:lQ,clearcoat_normal_fragment_maps:dQ,clearcoat_pars_fragment:cQ,iridescence_pars_fragment:nQ,opaque_fragment:sQ,packing:iQ,premultiplied_alpha_fragment:oQ,project_vertex:aQ,dithering_fragment:rQ,dithering_pars_fragment:tQ,roughnessmap_fragment:eQ,roughnessmap_pars_fragment:JZ,shadowmap_pars_fragment:$Z,shadowmap_pars_vertex:QZ,shadowmap_vertex:ZZ,shadowmask_pars_fragment:WZ,skinbase_vertex:YZ,skinning_pars_vertex:HZ,skinning_vertex:XZ,skinnormal_vertex:KZ,specularmap_fragment:GZ,specularmap_pars_fragment:UZ,tonemapping_fragment:qZ,tonemapping_pars_fragment:EZ,transmission_fragment:VZ,transmission_pars_fragment:FZ,uv_pars_fragment:DZ,uv_pars_vertex:RZ,uv_vertex:NZ,worldpos_vertex:OZ,background_vert:MZ,background_frag:BZ,backgroundCube_vert:zZ,backgroundCube_frag:kZ,cube_vert:AZ,cube_frag:wZ,depth_vert:LZ,depth_frag:_Z,distanceRGBA_vert:CZ,distanceRGBA_frag:PZ,equirect_vert:TZ,equirect_frag:IZ,linedashed_vert:SZ,linedashed_frag:yZ,meshbasic_vert:vZ,meshbasic_frag:jZ,meshlambert_vert:fZ,meshlambert_frag:hZ,meshmatcap_vert:bZ,meshmatcap_frag:xZ,meshnormal_vert:pZ,meshnormal_frag:gZ,meshphong_vert:mZ,meshphong_frag:uZ,meshphysical_vert:lZ,meshphysical_frag:dZ,meshtoon_vert:cZ,meshtoon_frag:nZ,points_vert:sZ,points_frag:iZ,shadow_vert:oZ,shadow_frag:aZ,sprite_vert:rZ,sprite_frag:tZ},HJ={common:{diffuse:{value:new nJ(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new jJ},alphaMap:{value:null},alphaMapTransform:{value:new jJ},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new jJ}},envmap:{envMap:{value:null},envMapRotation:{value:new jJ},flipEnvMap:{value:-1},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:0.98}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new jJ}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new jJ}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new jJ},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new jJ},normalScale:{value:new uJ(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new jJ},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new jJ}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new jJ}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new jJ}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:0.00025},fogNear:{value:1},fogFar:{value:2000},fogColor:{value:new nJ(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMap:{value:[]},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotShadowMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMap:{value:[]},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null}},points:{diffuse:{value:new nJ(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new jJ},alphaTest:{value:0},uvTransform:{value:new jJ}},sprite:{diffuse:{value:new nJ(16777215)},opacity:{value:1},center:{value:new uJ(0.5,0.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new jJ},alphaMap:{value:null},alphaMapTransform:{value:new jJ},alphaTest:{value:0}}},b0={basic:{uniforms:O0([HJ.common,HJ.specularmap,HJ.envmap,HJ.aomap,HJ.lightmap,HJ.fog]),vertexShader:bJ.meshbasic_vert,fragmentShader:bJ.meshbasic_frag},lambert:{uniforms:O0([HJ.common,HJ.specularmap,HJ.envmap,HJ.aomap,HJ.lightmap,HJ.emissivemap,HJ.bumpmap,HJ.normalmap,HJ.displacementmap,HJ.fog,HJ.lights,{emissive:{value:new nJ(0)}}]),vertexShader:bJ.meshlambert_vert,fragmentShader:bJ.meshlambert_frag},phong:{uniforms:O0([HJ.common,HJ.specularmap,HJ.envmap,HJ.aomap,HJ.lightmap,HJ.emissivemap,HJ.bumpmap,HJ.normalmap,HJ.displacementmap,HJ.fog,HJ.lights,{emissive:{value:new nJ(0)},specular:{value:new nJ(1118481)},shininess:{value:30}}]),vertexShader:bJ.meshphong_vert,fragmentShader:bJ.meshphong_frag},standard:{uniforms:O0([HJ.common,HJ.envmap,HJ.aomap,HJ.lightmap,HJ.emissivemap,HJ.bumpmap,HJ.normalmap,HJ.displacementmap,HJ.roughnessmap,HJ.metalnessmap,HJ.fog,HJ.lights,{emissive:{value:new nJ(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:bJ.meshphysical_vert,fragmentShader:bJ.meshphysical_frag},toon:{uniforms:O0([HJ.common,HJ.aomap,HJ.lightmap,HJ.emissivemap,HJ.bumpmap,HJ.normalmap,HJ.displacementmap,HJ.gradientmap,HJ.fog,HJ.lights,{emissive:{value:new nJ(0)}}]),vertexShader:bJ.meshtoon_vert,fragmentShader:bJ.meshtoon_frag},matcap:{uniforms:O0([HJ.common,HJ.bumpmap,HJ.normalmap,HJ.displacementmap,HJ.fog,{matcap:{value:null}}]),vertexShader:bJ.meshmatcap_vert,fragmentShader:bJ.meshmatcap_frag},points:{uniforms:O0([HJ.points,HJ.fog]),vertexShader:bJ.points_vert,fragmentShader:bJ.points_frag},dashed:{uniforms:O0([HJ.common,HJ.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:bJ.linedashed_vert,fragmentShader:bJ.linedashed_frag},depth:{uniforms:O0([HJ.common,HJ.displacementmap]),vertexShader:bJ.depth_vert,fragmentShader:bJ.depth_frag},normal:{uniforms:O0([HJ.common,HJ.bumpmap,HJ.normalmap,HJ.displacementmap,{opacity:{value:1}}]),vertexShader:bJ.meshnormal_vert,fragmentShader:bJ.meshnormal_frag},sprite:{uniforms:O0([HJ.sprite,HJ.fog]),vertexShader:bJ.sprite_vert,fragmentShader:bJ.sprite_frag},background:{uniforms:{uvTransform:{value:new jJ},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:bJ.background_vert,fragmentShader:bJ.background_frag},backgroundCube:{uniforms:{envMap:{value:null},flipEnvMap:{value:-1},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new jJ}},vertexShader:bJ.backgroundCube_vert,fragmentShader:bJ.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:bJ.cube_vert,fragmentShader:bJ.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:bJ.equirect_vert,fragmentShader:bJ.equirect_frag},distanceRGBA:{uniforms:O0([HJ.common,HJ.displacementmap,{referencePosition:{value:new v},nearDistance:{value:1},farDistance:{value:1000}}]),vertexShader:bJ.distanceRGBA_vert,fragmentShader:bJ.distanceRGBA_frag},shadow:{uniforms:O0([HJ.lights,HJ.fog,{color:{value:new nJ(0)},opacity:{value:1}}]),vertexShader:bJ.shadow_vert,fragmentShader:bJ.shadow_frag}};b0.physical={uniforms:O0([b0.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new jJ},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new jJ},clearcoatNormalScale:{value:new uJ(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new jJ},dispersion:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new jJ},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new jJ},sheen:{value:0},sheenColor:{value:new nJ(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new jJ},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new jJ},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new jJ},transmissionSamplerSize:{value:new uJ},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new jJ},attenuationDistance:{value:0},attenuationColor:{value:new nJ(0)},specularColor:{value:new nJ(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new jJ},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new jJ},anisotropyVector:{value:new uJ},anisotropyMap:{value:null},anisotropyMapTransform:{value:new jJ}}]),vertexShader:bJ.meshphysical_vert,fragmentShader:bJ.meshphysical_frag};var T7={r:0,b:0,g:0},F6=new o0,eZ=new Z0;function JW(J,$,Q,Z,W,Y,X){let H=new nJ(0),K=Y===!0?0:1,G,E,U=null,q=0,D=null;function N(A){let z=A.isScene===!0?A.background:null;if(z&&z.isTexture)z=(A.backgroundBlurriness>0?Q:$).get(z);return z}function O(A){let z=!1,_=N(A);if(_===null)F(H,K);else if(_&&_.isColor)F(_,1),z=!0;let b=J.xr.getEnvironmentBlendMode();if(b==="additive")Z.buffers.color.setClear(0,0,0,1,X);else if(b==="alpha-blend")Z.buffers.color.setClear(0,0,0,0,X);if(J.autoClear||z)Z.buffers.depth.setTest(!0),Z.buffers.depth.setMask(!0),Z.buffers.color.setMask(!0),J.clear(J.autoClearColor,J.autoClearDepth,J.autoClearStencil)}function V(A,z){let _=N(z);if(_&&(_.isCubeTexture||_.mapping===306)){if(E===void 0)E=new T0(new X0(1,1,1),new a0({name:"BackgroundCubeMaterial",uniforms:m6(b0.backgroundCube.uniforms),vertexShader:b0.backgroundCube.vertexShader,fragmentShader:b0.backgroundCube.fragmentShader,side:1,depthTest:!1,depthWrite:!1,fog:!1})),E.geometry.deleteAttribute("normal"),E.geometry.deleteAttribute("uv"),E.onBeforeRender=function(b,L,P){this.matrixWorld.copyPosition(P.matrixWorld)},Object.defineProperty(E.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),W.update(E);if(F6.copy(z.backgroundRotation),F6.x*=-1,F6.y*=-1,F6.z*=-1,_.isCubeTexture&&_.isRenderTargetTexture===!1)F6.y*=-1,F6.z*=-1;if(E.material.uniforms.envMap.value=_,E.material.uniforms.flipEnvMap.value=_.isCubeTexture&&_.isRenderTargetTexture===!1?-1:1,E.material.uniforms.backgroundBlurriness.value=z.backgroundBlurriness,E.material.uniforms.backgroundIntensity.value=z.backgroundIntensity,E.material.uniforms.backgroundRotation.value.setFromMatrix4(eZ.makeRotationFromEuler(F6)),E.material.toneMapped=dJ.getTransfer(_.colorSpace)!=="srgb",U!==_||q!==_.version||D!==J.toneMapping)E.material.needsUpdate=!0,U=_,q=_.version,D=J.toneMapping;E.layers.enableAll(),A.unshift(E,E.geometry,E.material,0,0,null)}else if(_&&_.isTexture){if(G===void 0)G=new T0(new a7(2,2),new a0({name:"BackgroundMaterial",uniforms:m6(b0.background.uniforms),vertexShader:b0.background.vertexShader,fragmentShader:b0.background.fragmentShader,side:0,depthTest:!1,depthWrite:!1,fog:!1})),G.geometry.deleteAttribute("normal"),Object.defineProperty(G.material,"map",{get:function(){return this.uniforms.t2D.value}}),W.update(G);if(G.material.uniforms.t2D.value=_,G.material.uniforms.backgroundIntensity.value=z.backgroundIntensity,G.material.toneMapped=dJ.getTransfer(_.colorSpace)!=="srgb",_.matrixAutoUpdate===!0)_.updateMatrix();if(G.material.uniforms.uvTransform.value.copy(_.matrix),U!==_||q!==_.version||D!==J.toneMapping)G.material.needsUpdate=!0,U=_,q=_.version,D=J.toneMapping;G.layers.enableAll(),A.unshift(G,G.geometry,G.material,0,0,null)}}function F(A,z){A.getRGB(T7,F$(J)),Z.buffers.color.setClear(T7.r,T7.g,T7.b,z,X)}return{getClearColor:function(){return H},setClearColor:function(A,z=1){H.set(A),K=z,F(H,K)},getClearAlpha:function(){return K},setClearAlpha:function(A){K=A,F(H,K)},render:O,addToRenderList:V}}function $W(J,$){let Q=J.getParameter(J.MAX_VERTEX_ATTRIBS),Z={},W=q(null),Y=W,X=!1;function H(k,T,x,m,u){let a=!1,l=U(m,x,T);if(Y!==l)Y=l,G(Y.object);if(a=D(k,m,x,u),a)N(k,m,x,u);if(u!==null)$.update(u,J.ELEMENT_ARRAY_BUFFER);if(a||X){if(X=!1,_(k,T,x,m),u!==null)J.bindBuffer(J.ELEMENT_ARRAY_BUFFER,$.get(u).buffer)}}function K(){return J.createVertexArray()}function G(k){return J.bindVertexArray(k)}function E(k){return J.deleteVertexArray(k)}function U(k,T,x){let m=x.wireframe===!0,u=Z[k.id];if(u===void 0)u={},Z[k.id]=u;let a=u[T.id];if(a===void 0)a={},u[T.id]=a;let l=a[m];if(l===void 0)l=q(K()),a[m]=l;return l}function q(k){let T=[],x=[],m=[];for(let u=0;u<Q;u++)T[u]=0,x[u]=0,m[u]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:T,enabledAttributes:x,attributeDivisors:m,object:k,attributes:{},index:null}}function D(k,T,x,m){let u=Y.attributes,a=T.attributes,l=0,t=x.getAttributes();for(let g in t)if(t[g].location>=0){let ZJ=u[g],_J=a[g];if(_J===void 0){if(g==="instanceMatrix"&&k.instanceMatrix)_J=k.instanceMatrix;if(g==="instanceColor"&&k.instanceColor)_J=k.instanceColor}if(ZJ===void 0)return!0;if(ZJ.attribute!==_J)return!0;if(_J&&ZJ.data!==_J.data)return!0;l++}if(Y.attributesNum!==l)return!0;if(Y.index!==m)return!0;return!1}function N(k,T,x,m){let u={},a=T.attributes,l=0,t=x.getAttributes();for(let g in t)if(t[g].location>=0){let ZJ=a[g];if(ZJ===void 0){if(g==="instanceMatrix"&&k.instanceMatrix)ZJ=k.instanceMatrix;if(g==="instanceColor"&&k.instanceColor)ZJ=k.instanceColor}let _J={};if(_J.attribute=ZJ,ZJ&&ZJ.data)_J.data=ZJ.data;u[g]=_J,l++}Y.attributes=u,Y.attributesNum=l,Y.index=m}function O(){let k=Y.newAttributes;for(let T=0,x=k.length;T<x;T++)k[T]=0}function V(k){F(k,0)}function F(k,T){let{newAttributes:x,enabledAttributes:m,attributeDivisors:u}=Y;if(x[k]=1,m[k]===0)J.enableVertexAttribArray(k),m[k]=1;if(u[k]!==T)J.vertexAttribDivisor(k,T),u[k]=T}function A(){let{newAttributes:k,enabledAttributes:T}=Y;for(let x=0,m=T.length;x<m;x++)if(T[x]!==k[x])J.disableVertexAttribArray(x),T[x]=0}function z(k,T,x,m,u,a,l){if(l===!0)J.vertexAttribIPointer(k,T,x,u,a);else J.vertexAttribPointer(k,T,x,m,u,a)}function _(k,T,x,m){O();let u=m.attributes,a=x.getAttributes(),l=T.defaultAttributeValues;for(let t in a){let g=a[t];if(g.location>=0){let XJ=u[t];if(XJ===void 0){if(t==="instanceMatrix"&&k.instanceMatrix)XJ=k.instanceMatrix;if(t==="instanceColor"&&k.instanceColor)XJ=k.instanceColor}if(XJ!==void 0){let{normalized:ZJ,itemSize:_J}=XJ,fJ=$.get(XJ);if(fJ===void 0)continue;let{buffer:n,type:e,bytesPerElement:zJ}=fJ,kJ=e===J.INT||e===J.UNSIGNED_INT||XJ.gpuType===1013;if(XJ.isInterleavedBufferAttribute){let YJ=XJ.data,d=YJ.stride,KJ=XJ.offset;if(YJ.isInstancedInterleavedBuffer){for(let WJ=0;WJ<g.locationSize;WJ++)F(g.location+WJ,YJ.meshPerAttribute);if(k.isInstancedMesh!==!0&&m._maxInstanceCount===void 0)m._maxInstanceCount=YJ.meshPerAttribute*YJ.count}else for(let WJ=0;WJ<g.locationSize;WJ++)V(g.location+WJ);J.bindBuffer(J.ARRAY_BUFFER,n);for(let WJ=0;WJ<g.locationSize;WJ++)z(g.location+WJ,_J/g.locationSize,e,ZJ,d*zJ,(KJ+_J/g.locationSize*WJ)*zJ,kJ)}else{if(XJ.isInstancedBufferAttribute){for(let YJ=0;YJ<g.locationSize;YJ++)F(g.location+YJ,XJ.meshPerAttribute);if(k.isInstancedMesh!==!0&&m._maxInstanceCount===void 0)m._maxInstanceCount=XJ.meshPerAttribute*XJ.count}else for(let YJ=0;YJ<g.locationSize;YJ++)V(g.location+YJ);J.bindBuffer(J.ARRAY_BUFFER,n);for(let YJ=0;YJ<g.locationSize;YJ++)z(g.location+YJ,_J/g.locationSize,e,ZJ,_J*zJ,_J/g.locationSize*YJ*zJ,kJ)}}else if(l!==void 0){let ZJ=l[t];if(ZJ!==void 0)switch(ZJ.length){case 2:J.vertexAttrib2fv(g.location,ZJ);break;case 3:J.vertexAttrib3fv(g.location,ZJ);break;case 4:J.vertexAttrib4fv(g.location,ZJ);break;default:J.vertexAttrib1fv(g.location,ZJ)}}}}A()}function b(){p();for(let k in Z){let T=Z[k];for(let x in T){let m=T[x];for(let u in m)E(m[u].object),delete m[u];delete T[x]}delete Z[k]}}function L(k){if(Z[k.id]===void 0)return;let T=Z[k.id];for(let x in T){let m=T[x];for(let u in m)E(m[u].object),delete m[u];delete T[x]}delete Z[k.id]}function P(k){for(let T in Z){let x=Z[T];if(x[k.id]===void 0)continue;let m=x[k.id];for(let u in m)E(m[u].object),delete m[u];delete x[k.id]}}function p(){if(B(),X=!0,Y===W)return;Y=W,G(Y.object)}function B(){W.geometry=null,W.program=null,W.wireframe=!1}return{setup:H,reset:p,resetDefaultState:B,dispose:b,releaseStatesOfGeometry:L,releaseStatesOfProgram:P,initAttributes:O,enableAttribute:V,disableUnusedAttributes:A}}function QW(J,$,Q){let Z;function W(G){Z=G}function Y(G,E){J.drawArrays(Z,G,E),Q.update(E,Z,1)}function X(G,E,U){if(U===0)return;J.drawArraysInstanced(Z,G,E,U),Q.update(E,Z,U)}function H(G,E,U){if(U===0)return;$.get("WEBGL_multi_draw").multiDrawArraysWEBGL(Z,G,0,E,0,U);let D=0;for(let N=0;N<U;N++)D+=E[N];Q.update(D,Z,1)}function K(G,E,U,q){if(U===0)return;let D=$.get("WEBGL_multi_draw");if(D===null)for(let N=0;N<G.length;N++)X(G[N],E[N],q[N]);else{D.multiDrawArraysInstancedWEBGL(Z,G,0,E,0,q,0,U);let N=0;for(let O=0;O<U;O++)N+=E[O]*q[O];Q.update(N,Z,1)}}this.setMode=W,this.render=Y,this.renderInstances=X,this.renderMultiDraw=H,this.renderMultiDrawInstances=K}function ZW(J,$,Q,Z){let W;function Y(){if(W!==void 0)return W;if($.has("EXT_texture_filter_anisotropic")===!0){let P=$.get("EXT_texture_filter_anisotropic");W=J.getParameter(P.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else W=0;return W}function X(P){if(P!==1023&&Z.convert(P)!==J.getParameter(J.IMPLEMENTATION_COLOR_READ_FORMAT))return!1;return!0}function H(P){let p=P===1016&&($.has("EXT_color_buffer_half_float")||$.has("EXT_color_buffer_float"));if(P!==1009&&Z.convert(P)!==J.getParameter(J.IMPLEMENTATION_COLOR_READ_TYPE)&&P!==1015&&!p)return!1;return!0}function K(P){if(P==="highp"){if(J.getShaderPrecisionFormat(J.VERTEX_SHADER,J.HIGH_FLOAT).precision>0&&J.getShaderPrecisionFormat(J.FRAGMENT_SHADER,J.HIGH_FLOAT).precision>0)return"highp";P="mediump"}if(P==="mediump"){if(J.getShaderPrecisionFormat(J.VERTEX_SHADER,J.MEDIUM_FLOAT).precision>0&&J.getShaderPrecisionFormat(J.FRAGMENT_SHADER,J.MEDIUM_FLOAT).precision>0)return"mediump"}return"lowp"}let G=Q.precision!==void 0?Q.precision:"highp",E=K(G);if(E!==G)console.warn("THREE.WebGLRenderer:",G,"not supported, using",E,"instead."),G=E;let U=Q.logarithmicDepthBuffer===!0,q=Q.reverseDepthBuffer===!0&&$.has("EXT_clip_control"),D=J.getParameter(J.MAX_TEXTURE_IMAGE_UNITS),N=J.getParameter(J.MAX_VERTEX_TEXTURE_IMAGE_UNITS),O=J.getParameter(J.MAX_TEXTURE_SIZE),V=J.getParameter(J.MAX_CUBE_MAP_TEXTURE_SIZE),F=J.getParameter(J.MAX_VERTEX_ATTRIBS),A=J.getParameter(J.MAX_VERTEX_UNIFORM_VECTORS),z=J.getParameter(J.MAX_VARYING_VECTORS),_=J.getParameter(J.MAX_FRAGMENT_UNIFORM_VECTORS),b=N>0,L=J.getParameter(J.MAX_SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:Y,getMaxPrecision:K,textureFormatReadable:X,textureTypeReadable:H,precision:G,logarithmicDepthBuffer:U,reverseDepthBuffer:q,maxTextures:D,maxVertexTextures:N,maxTextureSize:O,maxCubemapSize:V,maxAttributes:F,maxVertexUniforms:A,maxVaryings:z,maxFragmentUniforms:_,vertexTextures:b,maxSamples:L}}function WW(J){let $=this,Q=null,Z=0,W=!1,Y=!1,X=new Y6,H=new jJ,K={value:null,needsUpdate:!1};this.uniform=K,this.numPlanes=0,this.numIntersection=0,this.init=function(U,q){let D=U.length!==0||q||Z!==0||W;return W=q,Z=U.length,D},this.beginShadows=function(){Y=!0,E(null)},this.endShadows=function(){Y=!1},this.setGlobalState=function(U,q){Q=E(U,q,0)},this.setState=function(U,q,D){let{clippingPlanes:N,clipIntersection:O,clipShadows:V}=U,F=J.get(U);if(!W||N===null||N.length===0||Y&&!V)if(Y)E(null);else G();else{let A=Y?0:Z,z=A*4,_=F.clippingState||null;K.value=_,_=E(N,q,z,D);for(let b=0;b!==z;++b)_[b]=Q[b];F.clippingState=_,this.numIntersection=O?this.numPlanes:0,this.numPlanes+=A}};function G(){if(K.value!==Q)K.value=Q,K.needsUpdate=Z>0;$.numPlanes=Z,$.numIntersection=0}function E(U,q,D,N){let O=U!==null?U.length:0,V=null;if(O!==0){if(V=K.value,N!==!0||V===null){let F=D+O*4,A=q.matrixWorldInverse;if(H.getNormalMatrix(A),V===null||V.length<F)V=new Float32Array(F);for(let z=0,_=D;z!==O;++z,_+=4)X.copy(U[z]).applyMatrix4(A,H),X.normal.toArray(V,_),V[_+3]=X.constant}K.value=V,K.needsUpdate=!0}return $.numPlanes=O,$.numIntersection=0,V}}function YW(J){let $=new WeakMap;function Q(X,H){if(H===303)X.mapping=301;else if(H===304)X.mapping=302;return X}function Z(X){if(X&&X.isTexture){let H=X.mapping;if(H===303||H===304)if($.has(X)){let K=$.get(X).texture;return Q(K,X.mapping)}else{let K=X.image;if(K&&K.height>0){let G=new R$(K.height);return G.fromEquirectangularTexture(J,X),$.set(X,G),X.addEventListener("dispose",W),Q(G.texture,X.mapping)}else return null}}return X}function W(X){let H=X.target;H.removeEventListener("dispose",W);let K=$.get(H);if(K!==void 0)$.delete(H),K.dispose()}function Y(){$=new WeakMap}return{get:Z,dispose:Y}}class O$ extends u8{constructor(J=-1,$=1,Q=1,Z=-1,W=0.1,Y=2000){super();this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=J,this.right=$,this.top=Q,this.bottom=Z,this.near=W,this.far=Y,this.updateProjectionMatrix()}copy(J,$){return super.copy(J,$),this.left=J.left,this.right=J.right,this.top=J.top,this.bottom=J.bottom,this.near=J.near,this.far=J.far,this.zoom=J.zoom,this.view=J.view===null?null:Object.assign({},J.view),this}setViewOffset(J,$,Q,Z,W,Y){if(this.view===null)this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1};this.view.enabled=!0,this.view.fullWidth=J,this.view.fullHeight=$,this.view.offsetX=Q,this.view.offsetY=Z,this.view.width=W,this.view.height=Y,this.updateProjectionMatrix()}clearViewOffset(){if(this.view!==null)this.view.enabled=!1;this.updateProjectionMatrix()}updateProjectionMatrix(){let J=(this.right-this.left)/(2*this.zoom),$=(this.top-this.bottom)/(2*this.zoom),Q=(this.right+this.left)/2,Z=(this.top+this.bottom)/2,W=Q-J,Y=Q+J,X=Z+$,H=Z-$;if(this.view!==null&&this.view.enabled){let K=(this.right-this.left)/this.view.fullWidth/this.zoom,G=(this.top-this.bottom)/this.view.fullHeight/this.zoom;W+=K*this.view.offsetX,Y=W+K*this.view.width,X-=G*this.view.offsetY,H=X-G*this.view.height}this.projectionMatrix.makeOrthographic(W,Y,X,H,this.near,this.far,this.coordinateSystem),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(J){let $=super.toJSON(J);if($.object.zoom=this.zoom,$.object.left=this.left,$.object.right=this.right,$.object.top=this.top,$.object.bottom=this.bottom,$.object.near=this.near,$.object.far=this.far,this.view!==null)$.object.view=Object.assign({},this.view);return $}}var p6=4,I9=[0.125,0.215,0.35,0.446,0.526,0.582],N6=20,w8=new O$,S9=new nJ,L8=null,_8=0,C8=0,P8=!1,R6=(1+Math.sqrt(5))/2,j6=1/R6,y9=[new v(-R6,j6,0),new v(R6,j6,0),new v(-j6,0,R6),new v(j6,0,R6),new v(0,R6,-j6),new v(0,R6,j6),new v(-1,1,-1),new v(1,1,-1),new v(-1,1,1),new v(1,1,1)];class j8{constructor(J){this._renderer=J,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._lodPlanes=[],this._sizeLods=[],this._sigmas=[],this._blurMaterial=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._compileMaterial(this._blurMaterial)}fromScene(J,$=0,Q=0.1,Z=100){L8=this._renderer.getRenderTarget(),_8=this._renderer.getActiveCubeFace(),C8=this._renderer.getActiveMipmapLevel(),P8=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(256);let W=this._allocateTargets();if(W.depthBuffer=!0,this._sceneToCubeUV(J,Q,Z,W),$>0)this._blur(W,0,0,$);return this._applyPMREM(W),this._cleanup(W),W}fromEquirectangular(J,$=null){return this._fromTexture(J,$)}fromCubemap(J,$=null){return this._fromTexture(J,$)}compileCubemapShader(){if(this._cubemapMaterial===null)this._cubemapMaterial=f9(),this._compileMaterial(this._cubemapMaterial)}compileEquirectangularShader(){if(this._equirectMaterial===null)this._equirectMaterial=j9(),this._compileMaterial(this._equirectMaterial)}dispose(){if(this._dispose(),this._cubemapMaterial!==null)this._cubemapMaterial.dispose();if(this._equirectMaterial!==null)this._equirectMaterial.dispose()}_setSize(J){this._lodMax=Math.floor(Math.log2(J)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){if(this._blurMaterial!==null)this._blurMaterial.dispose();if(this._pingPongRenderTarget!==null)this._pingPongRenderTarget.dispose();for(let J=0;J<this._lodPlanes.length;J++)this._lodPlanes[J].dispose()}_cleanup(J){this._renderer.setRenderTarget(L8,_8,C8),this._renderer.xr.enabled=P8,J.scissorTest=!1,I7(J,0,0,J.width,J.height)}_fromTexture(J,$){if(J.mapping===301||J.mapping===302)this._setSize(J.image.length===0?16:J.image[0].width||J.image[0].image.width);else this._setSize(J.image.width/4);L8=this._renderer.getRenderTarget(),_8=this._renderer.getActiveCubeFace(),C8=this._renderer.getActiveMipmapLevel(),P8=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;let Q=$||this._allocateTargets();return this._textureToCubeUV(J,Q),this._applyPMREM(Q),this._cleanup(Q),Q}_allocateTargets(){let J=3*Math.max(this._cubeSize,112),$=4*this._cubeSize,Q={magFilter:1006,minFilter:1006,generateMipmaps:!1,type:1016,format:1023,colorSpace:"srgb-linear",depthBuffer:!1},Z=v9(J,$,Q);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==J||this._pingPongRenderTarget.height!==$){if(this._pingPongRenderTarget!==null)this._dispose();this._pingPongRenderTarget=v9(J,$,Q);let{_lodMax:W}=this;({sizeLods:this._sizeLods,lodPlanes:this._lodPlanes,sigmas:this._sigmas}=HW(W)),this._blurMaterial=XW(W,J,$)}return Z}_compileMaterial(J){let $=new T0(this._lodPlanes[0],J);this._renderer.compile($,w8)}_sceneToCubeUV(J,$,Q,Z){let X=new k0(90,1,$,Q),H=[1,-1,1,1,1,1],K=[1,1,1,-1,-1,-1],G=this._renderer,E=G.autoClear,U=G.toneMapping;G.getClearColor(S9),G.toneMapping=0,G.autoClear=!1;let q=new H7({name:"PMREM.Background",side:1,depthWrite:!1,depthTest:!1}),D=new T0(new X0,q),N=!1,O=J.background;if(O){if(O.isColor)q.color.copy(O),J.background=null,N=!0}else q.color.copy(S9),N=!0;for(let V=0;V<6;V++){let F=V%3;if(F===0)X.up.set(0,H[V],0),X.lookAt(K[V],0,0);else if(F===1)X.up.set(0,0,H[V]),X.lookAt(0,K[V],0);else X.up.set(0,H[V],0),X.lookAt(0,0,K[V]);let A=this._cubeSize;if(I7(Z,F*A,V>2?A:0,A,A),G.setRenderTarget(Z),N)G.render(D,X);G.render(J,X)}D.geometry.dispose(),D.material.dispose(),G.toneMapping=U,G.autoClear=E,J.background=O}_textureToCubeUV(J,$){let Q=this._renderer,Z=J.mapping===301||J.mapping===302;if(Z){if(this._cubemapMaterial===null)this._cubemapMaterial=f9();this._cubemapMaterial.uniforms.flipEnvMap.value=J.isRenderTargetTexture===!1?-1:1}else if(this._equirectMaterial===null)this._equirectMaterial=j9();let W=Z?this._cubemapMaterial:this._equirectMaterial,Y=new T0(this._lodPlanes[0],W),X=W.uniforms;X.envMap.value=J;let H=this._cubeSize;I7($,0,0,3*H,2*H),Q.setRenderTarget($),Q.render(Y,w8)}_applyPMREM(J){let $=this._renderer,Q=$.autoClear;$.autoClear=!1;let Z=this._lodPlanes.length;for(let W=1;W<Z;W++){let Y=Math.sqrt(this._sigmas[W]*this._sigmas[W]-this._sigmas[W-1]*this._sigmas[W-1]),X=y9[(Z-W-1)%y9.length];this._blur(J,W-1,W,Y,X)}$.autoClear=Q}_blur(J,$,Q,Z,W){let Y=this._pingPongRenderTarget;this._halfBlur(J,Y,$,Q,Z,"latitudinal",W),this._halfBlur(Y,J,Q,Q,Z,"longitudinal",W)}_halfBlur(J,$,Q,Z,W,Y,X){let H=this._renderer,K=this._blurMaterial;if(Y!=="latitudinal"&&Y!=="longitudinal")console.error("blur direction must be either latitudinal or longitudinal!");let G=3,E=new T0(this._lodPlanes[Z],K),U=K.uniforms,q=this._sizeLods[Q]-1,D=isFinite(W)?Math.PI/(2*q):2*Math.PI/(2*N6-1),N=W/D,O=isFinite(W)?1+Math.floor(G*N):N6;if(O>N6)console.warn(`sigmaRadians, ${W}, is too large and will clip, as it requested ${O} samples when the maximum is set to ${N6}`);let V=[],F=0;for(let L=0;L<N6;++L){let P=L/N,p=Math.exp(-P*P/2);if(V.push(p),L===0)F+=p;else if(L<O)F+=2*p}for(let L=0;L<V.length;L++)V[L]=V[L]/F;if(U.envMap.value=J.texture,U.samples.value=O,U.weights.value=V,U.latitudinal.value=Y==="latitudinal",X)U.poleAxis.value=X;let{_lodMax:A}=this;U.dTheta.value=D,U.mipInt.value=A-Q;let z=this._sizeLods[Z],_=3*z*(Z>A-p6?Z-A+p6:0),b=4*(this._cubeSize-z);I7($,_,b,3*z,2*z),H.setRenderTarget($),H.render(E,w8)}}function HW(J){let $=[],Q=[],Z=[],W=J,Y=J-p6+1+I9.length;for(let X=0;X<Y;X++){let H=Math.pow(2,W);Q.push(H);let K=1/H;if(X>J-p6)K=I9[X-J+p6-1];else if(X===0)K=0;Z.push(K);let G=1/(H-2),E=-G,U=1+G,q=[E,E,U,E,U,U,E,E,U,U,E,U],D=6,N=6,O=3,V=2,F=1,A=new Float32Array(O*N*D),z=new Float32Array(V*N*D),_=new Float32Array(F*N*D);for(let L=0;L<D;L++){let P=L%3*2/3-1,p=L>2?0:-1,B=[P,p,0,P+0.6666666666666666,p,0,P+0.6666666666666666,p+1,0,P,p,0,P+0.6666666666666666,p+1,0,P,p+1,0];A.set(B,O*N*L),z.set(q,V*N*L);let k=[L,L,L,L,L,L];_.set(k,F*N*L)}let b=new V0;if(b.setAttribute("position",new I0(A,O)),b.setAttribute("uv",new I0(z,V)),b.setAttribute("faceIndex",new I0(_,F)),$.push(b),W>p6)W--}return{lodPlanes:$,sizeLods:Q,sigmas:Z}}function v9(J,$,Q){let Z=new X6(J,$,Q);return Z.texture.mapping=306,Z.texture.name="PMREM.cubeUv",Z.scissorTest=!0,Z}function I7(J,$,Q,Z,W){J.viewport.set($,Q,Z,W),J.scissor.set($,Q,Z,W)}function XW(J,$,Q){let Z=new Float32Array(N6),W=new v(0,1,0);return new a0({name:"SphericalGaussianBlur",defines:{n:N6,CUBEUV_TEXEL_WIDTH:1/$,CUBEUV_TEXEL_HEIGHT:1/Q,CUBEUV_MAX_MIP:`${J}.0`},uniforms:{envMap:{value:null},samples:{value:1},weights:{value:Z},latitudinal:{value:!1},dTheta:{value:0},mipInt:{value:0},poleAxis:{value:W}},vertexShader:c8(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform int samples;
			uniform float weights[ n ];
			uniform bool latitudinal;
			uniform float dTheta;
			uniform float mipInt;
			uniform vec3 poleAxis;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			vec3 getSample( float theta, vec3 axis ) {

				float cosTheta = cos( theta );
				// Rodrigues' axis-angle rotation
				vec3 sampleDirection = vOutputDirection * cosTheta
					+ cross( axis, vOutputDirection ) * sin( theta )
					+ axis * dot( axis, vOutputDirection ) * ( 1.0 - cosTheta );

				return bilinearCubeUV( envMap, sampleDirection, mipInt );

			}

			void main() {

				vec3 axis = latitudinal ? poleAxis : cross( poleAxis, vOutputDirection );

				if ( all( equal( axis, vec3( 0.0 ) ) ) ) {

					axis = vec3( vOutputDirection.z, 0.0, - vOutputDirection.x );

				}

				axis = normalize( axis );

				gl_FragColor = vec4( 0.0, 0.0, 0.0, 1.0 );
				gl_FragColor.rgb += weights[ 0 ] * getSample( 0.0, axis );

				for ( int i = 1; i < n; i++ ) {

					if ( i >= samples ) {

						break;

					}

					float theta = dTheta * float( i );
					gl_FragColor.rgb += weights[ i ] * getSample( -1.0 * theta, axis );
					gl_FragColor.rgb += weights[ i ] * getSample( theta, axis );

				}

			}
		`,blending:0,depthTest:!1,depthWrite:!1})}function j9(){return new a0({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:c8(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;

			#include <common>

			void main() {

				vec3 outputDirection = normalize( vOutputDirection );
				vec2 uv = equirectUv( outputDirection );

				gl_FragColor = vec4( texture2D ( envMap, uv ).rgb, 1.0 );

			}
		`,blending:0,depthTest:!1,depthWrite:!1})}function f9(){return new a0({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:c8(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:0,depthTest:!1,depthWrite:!1})}function c8(){return`

		precision mediump float;
		precision mediump int;

		attribute float faceIndex;

		varying vec3 vOutputDirection;

		// RH coordinate system; PMREM face-indexing convention
		vec3 getDirection( vec2 uv, float face ) {

			uv = 2.0 * uv - 1.0;

			vec3 direction = vec3( uv, 1.0 );

			if ( face == 0.0 ) {

				direction = direction.zyx; // ( 1, v, u ) pos x

			} else if ( face == 1.0 ) {

				direction = direction.xzy;
				direction.xz *= -1.0; // ( -u, 1, -v ) pos y

			} else if ( face == 2.0 ) {

				direction.x *= -1.0; // ( -u, v, 1 ) pos z

			} else if ( face == 3.0 ) {

				direction = direction.zyx;
				direction.xz *= -1.0; // ( -1, v, -u ) neg x

			} else if ( face == 4.0 ) {

				direction = direction.xzy;
				direction.xy *= -1.0; // ( -u, -1, v ) neg y

			} else if ( face == 5.0 ) {

				direction.z *= -1.0; // ( u, v, -1 ) neg z

			}

			return direction;

		}

		void main() {

			vOutputDirection = getDirection( uv, faceIndex );
			gl_Position = vec4( position, 1.0 );

		}
	`}function KW(J){let $=new WeakMap,Q=null;function Z(H){if(H&&H.isTexture){let K=H.mapping,G=K===303||K===304,E=K===301||K===302;if(G||E){let U=$.get(H),q=U!==void 0?U.texture.pmremVersion:0;if(H.isRenderTargetTexture&&H.pmremVersion!==q){if(Q===null)Q=new j8(J);return U=G?Q.fromEquirectangular(H,U):Q.fromCubemap(H,U),U.texture.pmremVersion=H.pmremVersion,$.set(H,U),U.texture}else if(U!==void 0)return U.texture;else{let D=H.image;if(G&&D&&D.height>0||E&&D&&W(D)){if(Q===null)Q=new j8(J);return U=G?Q.fromEquirectangular(H):Q.fromCubemap(H),U.texture.pmremVersion=H.pmremVersion,$.set(H,U),H.addEventListener("dispose",Y),U.texture}else return null}}}return H}function W(H){let K=0,G=6;for(let E=0;E<G;E++)if(H[E]!==void 0)K++;return K===G}function Y(H){let K=H.target;K.removeEventListener("dispose",Y);let G=$.get(K);if(G!==void 0)$.delete(K),G.dispose()}function X(){if($=new WeakMap,Q!==null)Q.dispose(),Q=null}return{get:Z,dispose:X}}function GW(J){let $={};function Q(Z){if($[Z]!==void 0)return $[Z];let W;switch(Z){case"WEBGL_depth_texture":W=J.getExtension("WEBGL_depth_texture")||J.getExtension("MOZ_WEBGL_depth_texture")||J.getExtension("WEBKIT_WEBGL_depth_texture");break;case"EXT_texture_filter_anisotropic":W=J.getExtension("EXT_texture_filter_anisotropic")||J.getExtension("MOZ_EXT_texture_filter_anisotropic")||J.getExtension("WEBKIT_EXT_texture_filter_anisotropic");break;case"WEBGL_compressed_texture_s3tc":W=J.getExtension("WEBGL_compressed_texture_s3tc")||J.getExtension("MOZ_WEBGL_compressed_texture_s3tc")||J.getExtension("WEBKIT_WEBGL_compressed_texture_s3tc");break;case"WEBGL_compressed_texture_pvrtc":W=J.getExtension("WEBGL_compressed_texture_pvrtc")||J.getExtension("WEBKIT_WEBGL_compressed_texture_pvrtc");break;default:W=J.getExtension(Z)}return $[Z]=W,W}return{has:function(Z){return Q(Z)!==null},init:function(){Q("EXT_color_buffer_float"),Q("WEBGL_clip_cull_distance"),Q("OES_texture_float_linear"),Q("EXT_color_buffer_half_float"),Q("WEBGL_multisampled_render_to_texture"),Q("WEBGL_render_shared_exponent")},get:function(Z){let W=Q(Z);if(W===null)Z7("THREE.WebGLRenderer: "+Z+" extension not supported.");return W}}}function UW(J,$,Q,Z){let W={},Y=new WeakMap;function X(U){let q=U.target;if(q.index!==null)$.remove(q.index);for(let N in q.attributes)$.remove(q.attributes[N]);for(let N in q.morphAttributes){let O=q.morphAttributes[N];for(let V=0,F=O.length;V<F;V++)$.remove(O[V])}q.removeEventListener("dispose",X),delete W[q.id];let D=Y.get(q);if(D)$.remove(D),Y.delete(q);if(Z.releaseStatesOfGeometry(q),q.isInstancedBufferGeometry===!0)delete q._maxInstanceCount;Q.memory.geometries--}function H(U,q){if(W[q.id]===!0)return q;return q.addEventListener("dispose",X),W[q.id]=!0,Q.memory.geometries++,q}function K(U){let q=U.attributes;for(let N in q)$.update(q[N],J.ARRAY_BUFFER);let D=U.morphAttributes;for(let N in D){let O=D[N];for(let V=0,F=O.length;V<F;V++)$.update(O[V],J.ARRAY_BUFFER)}}function G(U){let q=[],D=U.index,N=U.attributes.position,O=0;if(D!==null){let A=D.array;O=D.version;for(let z=0,_=A.length;z<_;z+=3){let b=A[z+0],L=A[z+1],P=A[z+2];q.push(b,L,L,P,P,b)}}else if(N!==void 0){let A=N.array;O=N.version;for(let z=0,_=A.length/3-1;z<_;z+=3){let b=z+0,L=z+1,P=z+2;q.push(b,L,L,P,P,b)}}else return;let V=new((G$(q))?m8:g8)(q,1);V.version=O;let F=Y.get(U);if(F)$.remove(F);Y.set(U,V)}function E(U){let q=Y.get(U);if(q){let D=U.index;if(D!==null){if(q.version<D.version)G(U)}}else G(U);return Y.get(U)}return{get:H,update:K,getWireframeAttribute:E}}function qW(J,$,Q){let Z;function W(q){Z=q}let Y,X;function H(q){Y=q.type,X=q.bytesPerElement}function K(q,D){J.drawElements(Z,D,Y,q*X),Q.update(D,Z,1)}function G(q,D,N){if(N===0)return;J.drawElementsInstanced(Z,D,Y,q*X,N),Q.update(D,Z,N)}function E(q,D,N){if(N===0)return;$.get("WEBGL_multi_draw").multiDrawElementsWEBGL(Z,D,0,Y,q,0,N);let V=0;for(let F=0;F<N;F++)V+=D[F];Q.update(V,Z,1)}function U(q,D,N,O){if(N===0)return;let V=$.get("WEBGL_multi_draw");if(V===null)for(let F=0;F<q.length;F++)G(q[F]/X,D[F],O[F]);else{V.multiDrawElementsInstancedWEBGL(Z,D,0,Y,q,0,O,0,N);let F=0;for(let A=0;A<N;A++)F+=D[A]*O[A];Q.update(F,Z,1)}}this.setMode=W,this.setIndex=H,this.render=K,this.renderInstances=G,this.renderMultiDraw=E,this.renderMultiDrawInstances=U}function EW(J){let $={geometries:0,textures:0},Q={frame:0,calls:0,triangles:0,points:0,lines:0};function Z(Y,X,H){switch(Q.calls++,X){case J.TRIANGLES:Q.triangles+=H*(Y/3);break;case J.LINES:Q.lines+=H*(Y/2);break;case J.LINE_STRIP:Q.lines+=H*(Y-1);break;case J.LINE_LOOP:Q.lines+=H*Y;break;case J.POINTS:Q.points+=H*Y;break;default:console.error("THREE.WebGLInfo: Unknown draw mode:",X);break}}function W(){Q.calls=0,Q.triangles=0,Q.points=0,Q.lines=0}return{memory:$,render:Q,programs:null,autoReset:!0,reset:W,update:Z}}function VW(J,$,Q){let Z=new WeakMap,W=new H0;function Y(X,H,K){let G=X.morphTargetInfluences,E=H.morphAttributes.position||H.morphAttributes.normal||H.morphAttributes.color,U=E!==void 0?E.length:0,q=Z.get(H);if(q===void 0||q.count!==U){let B=function(){P.dispose(),Z.delete(H),H.removeEventListener("dispose",B)};if(q!==void 0)q.texture.dispose();let D=H.morphAttributes.position!==void 0,N=H.morphAttributes.normal!==void 0,O=H.morphAttributes.color!==void 0,V=H.morphAttributes.position||[],F=H.morphAttributes.normal||[],A=H.morphAttributes.color||[],z=0;if(D===!0)z=1;if(N===!0)z=2;if(O===!0)z=3;let _=H.attributes.position.count*z,b=1;if(_>$.maxTextureSize)b=Math.ceil(_/$.maxTextureSize),_=$.maxTextureSize;let L=new Float32Array(_*b*4*U),P=new x8(L,_,b,U);P.type=1015,P.needsUpdate=!0;let p=z*4;for(let k=0;k<U;k++){let T=V[k],x=F[k],m=A[k],u=_*b*4*k;for(let a=0;a<T.count;a++){let l=a*p;if(D===!0)W.fromBufferAttribute(T,a),L[u+l+0]=W.x,L[u+l+1]=W.y,L[u+l+2]=W.z,L[u+l+3]=0;if(N===!0)W.fromBufferAttribute(x,a),L[u+l+4]=W.x,L[u+l+5]=W.y,L[u+l+6]=W.z,L[u+l+7]=0;if(O===!0)W.fromBufferAttribute(m,a),L[u+l+8]=W.x,L[u+l+9]=W.y,L[u+l+10]=W.z,L[u+l+11]=m.itemSize===4?W.w:1}}q={count:U,texture:P,size:new uJ(_,b)},Z.set(H,q),H.addEventListener("dispose",B)}if(X.isInstancedMesh===!0&&X.morphTexture!==null)K.getUniforms().setValue(J,"morphTexture",X.morphTexture,Q);else{let D=0;for(let O=0;O<G.length;O++)D+=G[O];let N=H.morphTargetsRelative?1:1-D;K.getUniforms().setValue(J,"morphTargetBaseInfluence",N),K.getUniforms().setValue(J,"morphTargetInfluences",G)}K.getUniforms().setValue(J,"morphTargetsTexture",q.texture,Q),K.getUniforms().setValue(J,"morphTargetsTextureSize",q.size)}return{update:Y}}function FW(J,$,Q,Z){let W=new WeakMap;function Y(K){let G=Z.render.frame,E=K.geometry,U=$.get(K,E);if(W.get(U)!==G)$.update(U),W.set(U,G);if(K.isInstancedMesh){if(K.hasEventListener("dispose",H)===!1)K.addEventListener("dispose",H);if(W.get(K)!==G){if(Q.update(K.instanceMatrix,J.ARRAY_BUFFER),K.instanceColor!==null)Q.update(K.instanceColor,J.ARRAY_BUFFER);W.set(K,G)}}if(K.isSkinnedMesh){let q=K.skeleton;if(W.get(q)!==G)q.update(),W.set(q,G)}return U}function X(){W=new WeakMap}function H(K){let G=K.target;if(G.removeEventListener("dispose",H),Q.remove(G.instanceMatrix),G.instanceColor!==null)Q.remove(G.instanceColor)}return{update:Y,dispose:X}}class n8 extends M0{constructor(J,$,Q,Z,W,Y,X,H,K,G=1026){if(G!==1026&&G!==1027)throw Error("DepthTexture format must be either THREE.DepthFormat or THREE.DepthStencilFormat");if(Q===void 0&&G===1026)Q=1014;if(Q===void 0&&G===1027)Q=1020;super(null,Z,W,Y,X,H,G,Q,K);this.isDepthTexture=!0,this.image={width:J,height:$},this.magFilter=X!==void 0?X:1003,this.minFilter=H!==void 0?H:1003,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(J){return super.copy(J),this.compareFunction=J.compareFunction,this}toJSON(J){let $=super.toJSON(J);if(this.compareFunction!==null)$.compareFunction=this.compareFunction;return $}}var M$=new M0,h9=new n8(1,1),B$=new x8,z$=new E$,k$=new l8,b9=[],x9=[],p9=new Float32Array(16),g9=new Float32Array(9),m9=new Float32Array(4);function d6(J,$,Q){let Z=J[0];if(Z<=0||Z>0)return J;let W=$*Q,Y=b9[W];if(Y===void 0)Y=new Float32Array(W),b9[W]=Y;if($!==0){Z.toArray(Y,0);for(let X=1,H=0;X!==$;++X)H+=Q,J[X].toArray(Y,H)}return Y}function G0(J,$){if(J.length!==$.length)return!1;for(let Q=0,Z=J.length;Q<Z;Q++)if(J[Q]!==$[Q])return!1;return!0}function U0(J,$){for(let Q=0,Z=$.length;Q<Z;Q++)J[Q]=$[Q]}function r7(J,$){let Q=x9[$];if(Q===void 0)Q=new Int32Array($),x9[$]=Q;for(let Z=0;Z!==$;++Z)Q[Z]=J.allocateTextureUnit();return Q}function DW(J,$){let Q=this.cache;if(Q[0]===$)return;J.uniform1f(this.addr,$),Q[0]=$}function RW(J,$){let Q=this.cache;if($.x!==void 0){if(Q[0]!==$.x||Q[1]!==$.y)J.uniform2f(this.addr,$.x,$.y),Q[0]=$.x,Q[1]=$.y}else{if(G0(Q,$))return;J.uniform2fv(this.addr,$),U0(Q,$)}}function NW(J,$){let Q=this.cache;if($.x!==void 0){if(Q[0]!==$.x||Q[1]!==$.y||Q[2]!==$.z)J.uniform3f(this.addr,$.x,$.y,$.z),Q[0]=$.x,Q[1]=$.y,Q[2]=$.z}else if($.r!==void 0){if(Q[0]!==$.r||Q[1]!==$.g||Q[2]!==$.b)J.uniform3f(this.addr,$.r,$.g,$.b),Q[0]=$.r,Q[1]=$.g,Q[2]=$.b}else{if(G0(Q,$))return;J.uniform3fv(this.addr,$),U0(Q,$)}}function OW(J,$){let Q=this.cache;if($.x!==void 0){if(Q[0]!==$.x||Q[1]!==$.y||Q[2]!==$.z||Q[3]!==$.w)J.uniform4f(this.addr,$.x,$.y,$.z,$.w),Q[0]=$.x,Q[1]=$.y,Q[2]=$.z,Q[3]=$.w}else{if(G0(Q,$))return;J.uniform4fv(this.addr,$),U0(Q,$)}}function MW(J,$){let Q=this.cache,Z=$.elements;if(Z===void 0){if(G0(Q,$))return;J.uniformMatrix2fv(this.addr,!1,$),U0(Q,$)}else{if(G0(Q,Z))return;m9.set(Z),J.uniformMatrix2fv(this.addr,!1,m9),U0(Q,Z)}}function BW(J,$){let Q=this.cache,Z=$.elements;if(Z===void 0){if(G0(Q,$))return;J.uniformMatrix3fv(this.addr,!1,$),U0(Q,$)}else{if(G0(Q,Z))return;g9.set(Z),J.uniformMatrix3fv(this.addr,!1,g9),U0(Q,Z)}}function zW(J,$){let Q=this.cache,Z=$.elements;if(Z===void 0){if(G0(Q,$))return;J.uniformMatrix4fv(this.addr,!1,$),U0(Q,$)}else{if(G0(Q,Z))return;p9.set(Z),J.uniformMatrix4fv(this.addr,!1,p9),U0(Q,Z)}}function kW(J,$){let Q=this.cache;if(Q[0]===$)return;J.uniform1i(this.addr,$),Q[0]=$}function AW(J,$){let Q=this.cache;if($.x!==void 0){if(Q[0]!==$.x||Q[1]!==$.y)J.uniform2i(this.addr,$.x,$.y),Q[0]=$.x,Q[1]=$.y}else{if(G0(Q,$))return;J.uniform2iv(this.addr,$),U0(Q,$)}}function wW(J,$){let Q=this.cache;if($.x!==void 0){if(Q[0]!==$.x||Q[1]!==$.y||Q[2]!==$.z)J.uniform3i(this.addr,$.x,$.y,$.z),Q[0]=$.x,Q[1]=$.y,Q[2]=$.z}else{if(G0(Q,$))return;J.uniform3iv(this.addr,$),U0(Q,$)}}function LW(J,$){let Q=this.cache;if($.x!==void 0){if(Q[0]!==$.x||Q[1]!==$.y||Q[2]!==$.z||Q[3]!==$.w)J.uniform4i(this.addr,$.x,$.y,$.z,$.w),Q[0]=$.x,Q[1]=$.y,Q[2]=$.z,Q[3]=$.w}else{if(G0(Q,$))return;J.uniform4iv(this.addr,$),U0(Q,$)}}function _W(J,$){let Q=this.cache;if(Q[0]===$)return;J.uniform1ui(this.addr,$),Q[0]=$}function CW(J,$){let Q=this.cache;if($.x!==void 0){if(Q[0]!==$.x||Q[1]!==$.y)J.uniform2ui(this.addr,$.x,$.y),Q[0]=$.x,Q[1]=$.y}else{if(G0(Q,$))return;J.uniform2uiv(this.addr,$),U0(Q,$)}}function PW(J,$){let Q=this.cache;if($.x!==void 0){if(Q[0]!==$.x||Q[1]!==$.y||Q[2]!==$.z)J.uniform3ui(this.addr,$.x,$.y,$.z),Q[0]=$.x,Q[1]=$.y,Q[2]=$.z}else{if(G0(Q,$))return;J.uniform3uiv(this.addr,$),U0(Q,$)}}function TW(J,$){let Q=this.cache;if($.x!==void 0){if(Q[0]!==$.x||Q[1]!==$.y||Q[2]!==$.z||Q[3]!==$.w)J.uniform4ui(this.addr,$.x,$.y,$.z,$.w),Q[0]=$.x,Q[1]=$.y,Q[2]=$.z,Q[3]=$.w}else{if(G0(Q,$))return;J.uniform4uiv(this.addr,$),U0(Q,$)}}function IW(J,$,Q){let Z=this.cache,W=Q.allocateTextureUnit();if(Z[0]!==W)J.uniform1i(this.addr,W),Z[0]=W;let Y;if(this.type===J.SAMPLER_2D_SHADOW)h9.compareFunction=515,Y=h9;else Y=M$;Q.setTexture2D($||Y,W)}function SW(J,$,Q){let Z=this.cache,W=Q.allocateTextureUnit();if(Z[0]!==W)J.uniform1i(this.addr,W),Z[0]=W;Q.setTexture3D($||z$,W)}function yW(J,$,Q){let Z=this.cache,W=Q.allocateTextureUnit();if(Z[0]!==W)J.uniform1i(this.addr,W),Z[0]=W;Q.setTextureCube($||k$,W)}function vW(J,$,Q){let Z=this.cache,W=Q.allocateTextureUnit();if(Z[0]!==W)J.uniform1i(this.addr,W),Z[0]=W;Q.setTexture2DArray($||B$,W)}function jW(J){switch(J){case 5126:return DW;case 35664:return RW;case 35665:return NW;case 35666:return OW;case 35674:return MW;case 35675:return BW;case 35676:return zW;case 5124:case 35670:return kW;case 35667:case 35671:return AW;case 35668:case 35672:return wW;case 35669:case 35673:return LW;case 5125:return _W;case 36294:return CW;case 36295:return PW;case 36296:return TW;case 35678:case 36198:case 36298:case 36306:case 35682:return IW;case 35679:case 36299:case 36307:return SW;case 35680:case 36300:case 36308:case 36293:return yW;case 36289:case 36303:case 36311:case 36292:return vW}}function fW(J,$){J.uniform1fv(this.addr,$)}function hW(J,$){let Q=d6($,this.size,2);J.uniform2fv(this.addr,Q)}function bW(J,$){let Q=d6($,this.size,3);J.uniform3fv(this.addr,Q)}function xW(J,$){let Q=d6($,this.size,4);J.uniform4fv(this.addr,Q)}function pW(J,$){let Q=d6($,this.size,4);J.uniformMatrix2fv(this.addr,!1,Q)}function gW(J,$){let Q=d6($,this.size,9);J.uniformMatrix3fv(this.addr,!1,Q)}function mW(J,$){let Q=d6($,this.size,16);J.uniformMatrix4fv(this.addr,!1,Q)}function uW(J,$){J.uniform1iv(this.addr,$)}function lW(J,$){J.uniform2iv(this.addr,$)}function dW(J,$){J.uniform3iv(this.addr,$)}function cW(J,$){J.uniform4iv(this.addr,$)}function nW(J,$){J.uniform1uiv(this.addr,$)}function sW(J,$){J.uniform2uiv(this.addr,$)}function iW(J,$){J.uniform3uiv(this.addr,$)}function oW(J,$){J.uniform4uiv(this.addr,$)}function aW(J,$,Q){let Z=this.cache,W=$.length,Y=r7(Q,W);if(!G0(Z,Y))J.uniform1iv(this.addr,Y),U0(Z,Y);for(let X=0;X!==W;++X)Q.setTexture2D($[X]||M$,Y[X])}function rW(J,$,Q){let Z=this.cache,W=$.length,Y=r7(Q,W);if(!G0(Z,Y))J.uniform1iv(this.addr,Y),U0(Z,Y);for(let X=0;X!==W;++X)Q.setTexture3D($[X]||z$,Y[X])}function tW(J,$,Q){let Z=this.cache,W=$.length,Y=r7(Q,W);if(!G0(Z,Y))J.uniform1iv(this.addr,Y),U0(Z,Y);for(let X=0;X!==W;++X)Q.setTextureCube($[X]||k$,Y[X])}function eW(J,$,Q){let Z=this.cache,W=$.length,Y=r7(Q,W);if(!G0(Z,Y))J.uniform1iv(this.addr,Y),U0(Z,Y);for(let X=0;X!==W;++X)Q.setTexture2DArray($[X]||B$,Y[X])}function J4(J){switch(J){case 5126:return fW;case 35664:return hW;case 35665:return bW;case 35666:return xW;case 35674:return pW;case 35675:return gW;case 35676:return mW;case 5124:case 35670:return uW;case 35667:case 35671:return lW;case 35668:case 35672:return dW;case 35669:case 35673:return cW;case 5125:return nW;case 36294:return sW;case 36295:return iW;case 36296:return oW;case 35678:case 36198:case 36298:case 36306:case 35682:return aW;case 35679:case 36299:case 36307:return rW;case 35680:case 36300:case 36308:case 36293:return tW;case 36289:case 36303:case 36311:case 36292:return eW}}class A${constructor(J,$,Q){this.id=J,this.addr=Q,this.cache=[],this.type=$.type,this.setValue=jW($.type)}}class w${constructor(J,$,Q){this.id=J,this.addr=Q,this.cache=[],this.type=$.type,this.size=$.size,this.setValue=J4($.type)}}class L${constructor(J){this.id=J,this.seq=[],this.map={}}setValue(J,$,Q){let Z=this.seq;for(let W=0,Y=Z.length;W!==Y;++W){let X=Z[W];X.setValue(J,$[X.id],Q)}}}var T8=/(\w+)(\])?(\[|\.)?/g;function u9(J,$){J.seq.push($),J.map[$.id]=$}function $4(J,$,Q){let Z=J.name,W=Z.length;T8.lastIndex=0;while(!0){let Y=T8.exec(Z),X=T8.lastIndex,H=Y[1],K=Y[2]==="]",G=Y[3];if(K)H=H|0;if(G===void 0||G==="["&&X+2===W){u9(Q,G===void 0?new A$(H,J,$):new w$(H,J,$));break}else{let U=Q.map[H];if(U===void 0)U=new L$(H),u9(Q,U);Q=U}}}class Y7{constructor(J,$){this.seq=[],this.map={};let Q=J.getProgramParameter($,J.ACTIVE_UNIFORMS);for(let Z=0;Z<Q;++Z){let W=J.getActiveUniform($,Z),Y=J.getUniformLocation($,W.name);$4(W,Y,this)}}setValue(J,$,Q,Z){let W=this.map[$];if(W!==void 0)W.setValue(J,Q,Z)}setOptional(J,$,Q){let Z=$[Q];if(Z!==void 0)this.setValue(J,Q,Z)}static upload(J,$,Q,Z){for(let W=0,Y=$.length;W!==Y;++W){let X=$[W],H=Q[X.id];if(H.needsUpdate!==!1)X.setValue(J,H.value,Z)}}static seqWithValue(J,$){let Q=[];for(let Z=0,W=J.length;Z!==W;++Z){let Y=J[Z];if(Y.id in $)Q.push(Y)}return Q}}function l9(J,$,Q){let Z=J.createShader($);return J.shaderSource(Z,Q),J.compileShader(Z),Z}var Q4=37297,Z4=0;function W4(J,$){let Q=J.split(`
`),Z=[],W=Math.max($-6,0),Y=Math.min($+6,Q.length);for(let X=W;X<Y;X++){let H=X+1;Z.push(`${H===$?">":" "} ${H}: ${Q[X]}`)}return Z.join(`
`)}var d9=new jJ;function Y4(J){dJ._getMatrix(d9,dJ.workingColorSpace,J);let $=`mat3( ${d9.elements.map((Q)=>Q.toFixed(4))} )`;switch(dJ.getTransfer(J)){case"linear":return[$,"LinearTransferOETF"];case"srgb":return[$,"sRGBTransferOETF"];default:return console.warn("THREE.WebGLProgram: Unsupported color space: ",J),[$,"LinearTransferOETF"]}}function c9(J,$,Q){let Z=J.getShaderParameter($,J.COMPILE_STATUS),W=J.getShaderInfoLog($).trim();if(Z&&W==="")return"";let Y=/ERROR: 0:(\d+)/.exec(W);if(Y){let X=parseInt(Y[1]);return Q.toUpperCase()+`

`+W+`

`+W4(J.getShaderSource($),X)}else return W}function H4(J,$){let Q=Y4($);return[`vec4 ${J}( vec4 value ) {`,`	return ${Q[1]}( vec4( value.rgb * ${Q[0]}, value.a ) );`,"}"].join(`
`)}function X4(J,$){let Q;switch($){case 1:Q="Linear";break;case 2:Q="Reinhard";break;case 3:Q="Cineon";break;case 4:Q="ACESFilmic";break;case 6:Q="AgX";break;case 7:Q="Neutral";break;case 5:Q="Custom";break;default:console.warn("THREE.WebGLProgram: Unsupported toneMapping:",$),Q="Linear"}return"vec3 "+J+"( vec3 color ) { return "+Q+"ToneMapping( color ); }"}var S7=new v;function K4(){dJ.getLuminanceCoefficients(S7);let J=S7.x.toFixed(4),$=S7.y.toFixed(4),Q=S7.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${J}, ${$}, ${Q} );`,"\treturn dot( weights, rgb );","}"].join(`
`)}function G4(J){return[J.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",J.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(W7).join(`
`)}function U4(J){let $=[];for(let Q in J){let Z=J[Q];if(Z===!1)continue;$.push("#define "+Q+" "+Z)}return $.join(`
`)}function q4(J,$){let Q={},Z=J.getProgramParameter($,J.ACTIVE_ATTRIBUTES);for(let W=0;W<Z;W++){let Y=J.getActiveAttrib($,W),X=Y.name,H=1;if(Y.type===J.FLOAT_MAT2)H=2;if(Y.type===J.FLOAT_MAT3)H=3;if(Y.type===J.FLOAT_MAT4)H=4;Q[X]={type:Y.type,location:J.getAttribLocation($,X),locationSize:H}}return Q}function W7(J){return J!==""}function n9(J,$){let Q=$.numSpotLightShadows+$.numSpotLightMaps-$.numSpotLightShadowsWithMaps;return J.replace(/NUM_DIR_LIGHTS/g,$.numDirLights).replace(/NUM_SPOT_LIGHTS/g,$.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,$.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,Q).replace(/NUM_RECT_AREA_LIGHTS/g,$.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,$.numPointLights).replace(/NUM_HEMI_LIGHTS/g,$.numHemiLights).replace(/NUM_DIR_LIGHT_SHADOWS/g,$.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,$.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,$.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,$.numPointLightShadows)}function s9(J,$){return J.replace(/NUM_CLIPPING_PLANES/g,$.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,$.numClippingPlanes-$.numClipIntersection)}var E4=/^[ \t]*#include +<([\w\d./]+)>/gm;function f8(J){return J.replace(E4,F4)}var V4=new Map;function F4(J,$){let Q=bJ[$];if(Q===void 0){let Z=V4.get($);if(Z!==void 0)Q=bJ[Z],console.warn('THREE.WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',$,Z);else throw Error("Can not resolve #include <"+$+">")}return f8(Q)}var D4=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function i9(J){return J.replace(D4,R4)}function R4(J,$,Q,Z){let W="";for(let Y=parseInt($);Y<parseInt(Q);Y++)W+=Z.replace(/\[\s*i\s*\]/g,"[ "+Y+" ]").replace(/UNROLLED_LOOP_INDEX/g,Y);return W}function o9(J){let $=`precision ${J.precision} float;
	precision ${J.precision} int;
	precision ${J.precision} sampler2D;
	precision ${J.precision} samplerCube;
	precision ${J.precision} sampler3D;
	precision ${J.precision} sampler2DArray;
	precision ${J.precision} sampler2DShadow;
	precision ${J.precision} samplerCubeShadow;
	precision ${J.precision} sampler2DArrayShadow;
	precision ${J.precision} isampler2D;
	precision ${J.precision} isampler3D;
	precision ${J.precision} isamplerCube;
	precision ${J.precision} isampler2DArray;
	precision ${J.precision} usampler2D;
	precision ${J.precision} usampler3D;
	precision ${J.precision} usamplerCube;
	precision ${J.precision} usampler2DArray;
	`;if(J.precision==="highp")$+=`
#define HIGH_PRECISION`;else if(J.precision==="mediump")$+=`
#define MEDIUM_PRECISION`;else if(J.precision==="lowp")$+=`
#define LOW_PRECISION`;return $}function N4(J){let $="SHADOWMAP_TYPE_BASIC";if(J.shadowMapType===1)$="SHADOWMAP_TYPE_PCF";else if(J.shadowMapType===2)$="SHADOWMAP_TYPE_PCF_SOFT";else if(J.shadowMapType===3)$="SHADOWMAP_TYPE_VSM";return $}function O4(J){let $="ENVMAP_TYPE_CUBE";if(J.envMap)switch(J.envMapMode){case 301:case 302:$="ENVMAP_TYPE_CUBE";break;case 306:$="ENVMAP_TYPE_CUBE_UV";break}return $}function M4(J){let $="ENVMAP_MODE_REFLECTION";if(J.envMap)switch(J.envMapMode){case 302:$="ENVMAP_MODE_REFRACTION";break}return $}function B4(J){let $="ENVMAP_BLENDING_NONE";if(J.envMap)switch(J.combine){case 0:$="ENVMAP_BLENDING_MULTIPLY";break;case 1:$="ENVMAP_BLENDING_MIX";break;case 2:$="ENVMAP_BLENDING_ADD";break}return $}function z4(J){let $=J.envMapCubeUVHeight;if($===null)return null;let Q=Math.log2($)-2,Z=1/$;return{texelWidth:1/(3*Math.max(Math.pow(2,Q),112)),texelHeight:Z,maxMip:Q}}function k4(J,$,Q,Z){let W=J.getContext(),Y=Q.defines,X=Q.vertexShader,H=Q.fragmentShader,K=N4(Q),G=O4(Q),E=M4(Q),U=B4(Q),q=z4(Q),D=G4(Q),N=U4(Y),O=W.createProgram(),V,F,A=Q.glslVersion?"#version "+Q.glslVersion+`
`:"";if(Q.isRawShaderMaterial){if(V=["#define SHADER_TYPE "+Q.shaderType,"#define SHADER_NAME "+Q.shaderName,N].filter(W7).join(`
`),V.length>0)V+=`
`;if(F=["#define SHADER_TYPE "+Q.shaderType,"#define SHADER_NAME "+Q.shaderName,N].filter(W7).join(`
`),F.length>0)F+=`
`}else V=[o9(Q),"#define SHADER_TYPE "+Q.shaderType,"#define SHADER_NAME "+Q.shaderName,N,Q.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",Q.batching?"#define USE_BATCHING":"",Q.batchingColor?"#define USE_BATCHING_COLOR":"",Q.instancing?"#define USE_INSTANCING":"",Q.instancingColor?"#define USE_INSTANCING_COLOR":"",Q.instancingMorph?"#define USE_INSTANCING_MORPH":"",Q.useFog&&Q.fog?"#define USE_FOG":"",Q.useFog&&Q.fogExp2?"#define FOG_EXP2":"",Q.map?"#define USE_MAP":"",Q.envMap?"#define USE_ENVMAP":"",Q.envMap?"#define "+E:"",Q.lightMap?"#define USE_LIGHTMAP":"",Q.aoMap?"#define USE_AOMAP":"",Q.bumpMap?"#define USE_BUMPMAP":"",Q.normalMap?"#define USE_NORMALMAP":"",Q.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",Q.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",Q.displacementMap?"#define USE_DISPLACEMENTMAP":"",Q.emissiveMap?"#define USE_EMISSIVEMAP":"",Q.anisotropy?"#define USE_ANISOTROPY":"",Q.anisotropyMap?"#define USE_ANISOTROPYMAP":"",Q.clearcoatMap?"#define USE_CLEARCOATMAP":"",Q.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",Q.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",Q.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",Q.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",Q.specularMap?"#define USE_SPECULARMAP":"",Q.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",Q.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",Q.roughnessMap?"#define USE_ROUGHNESSMAP":"",Q.metalnessMap?"#define USE_METALNESSMAP":"",Q.alphaMap?"#define USE_ALPHAMAP":"",Q.alphaHash?"#define USE_ALPHAHASH":"",Q.transmission?"#define USE_TRANSMISSION":"",Q.transmissionMap?"#define USE_TRANSMISSIONMAP":"",Q.thicknessMap?"#define USE_THICKNESSMAP":"",Q.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",Q.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",Q.mapUv?"#define MAP_UV "+Q.mapUv:"",Q.alphaMapUv?"#define ALPHAMAP_UV "+Q.alphaMapUv:"",Q.lightMapUv?"#define LIGHTMAP_UV "+Q.lightMapUv:"",Q.aoMapUv?"#define AOMAP_UV "+Q.aoMapUv:"",Q.emissiveMapUv?"#define EMISSIVEMAP_UV "+Q.emissiveMapUv:"",Q.bumpMapUv?"#define BUMPMAP_UV "+Q.bumpMapUv:"",Q.normalMapUv?"#define NORMALMAP_UV "+Q.normalMapUv:"",Q.displacementMapUv?"#define DISPLACEMENTMAP_UV "+Q.displacementMapUv:"",Q.metalnessMapUv?"#define METALNESSMAP_UV "+Q.metalnessMapUv:"",Q.roughnessMapUv?"#define ROUGHNESSMAP_UV "+Q.roughnessMapUv:"",Q.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+Q.anisotropyMapUv:"",Q.clearcoatMapUv?"#define CLEARCOATMAP_UV "+Q.clearcoatMapUv:"",Q.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+Q.clearcoatNormalMapUv:"",Q.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+Q.clearcoatRoughnessMapUv:"",Q.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+Q.iridescenceMapUv:"",Q.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+Q.iridescenceThicknessMapUv:"",Q.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+Q.sheenColorMapUv:"",Q.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+Q.sheenRoughnessMapUv:"",Q.specularMapUv?"#define SPECULARMAP_UV "+Q.specularMapUv:"",Q.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+Q.specularColorMapUv:"",Q.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+Q.specularIntensityMapUv:"",Q.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+Q.transmissionMapUv:"",Q.thicknessMapUv?"#define THICKNESSMAP_UV "+Q.thicknessMapUv:"",Q.vertexTangents&&Q.flatShading===!1?"#define USE_TANGENT":"",Q.vertexColors?"#define USE_COLOR":"",Q.vertexAlphas?"#define USE_COLOR_ALPHA":"",Q.vertexUv1s?"#define USE_UV1":"",Q.vertexUv2s?"#define USE_UV2":"",Q.vertexUv3s?"#define USE_UV3":"",Q.pointsUvs?"#define USE_POINTS_UV":"",Q.flatShading?"#define FLAT_SHADED":"",Q.skinning?"#define USE_SKINNING":"",Q.morphTargets?"#define USE_MORPHTARGETS":"",Q.morphNormals&&Q.flatShading===!1?"#define USE_MORPHNORMALS":"",Q.morphColors?"#define USE_MORPHCOLORS":"",Q.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+Q.morphTextureStride:"",Q.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+Q.morphTargetsCount:"",Q.doubleSided?"#define DOUBLE_SIDED":"",Q.flipSided?"#define FLIP_SIDED":"",Q.shadowMapEnabled?"#define USE_SHADOWMAP":"",Q.shadowMapEnabled?"#define "+K:"",Q.sizeAttenuation?"#define USE_SIZEATTENUATION":"",Q.numLightProbes>0?"#define USE_LIGHT_PROBES":"",Q.logarithmicDepthBuffer?"#define USE_LOGDEPTHBUF":"",Q.reverseDepthBuffer?"#define USE_REVERSEDEPTHBUF":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","\tattribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","\tattribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","\tuniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","\tattribute vec2 uv1;","#endif","#ifdef USE_UV2","\tattribute vec2 uv2;","#endif","#ifdef USE_UV3","\tattribute vec2 uv3;","#endif","#ifdef USE_TANGENT","\tattribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","\tattribute vec4 color;","#elif defined( USE_COLOR )","\tattribute vec3 color;","#endif","#ifdef USE_SKINNING","\tattribute vec4 skinIndex;","\tattribute vec4 skinWeight;","#endif",`
`].filter(W7).join(`
`),F=[o9(Q),"#define SHADER_TYPE "+Q.shaderType,"#define SHADER_NAME "+Q.shaderName,N,Q.useFog&&Q.fog?"#define USE_FOG":"",Q.useFog&&Q.fogExp2?"#define FOG_EXP2":"",Q.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",Q.map?"#define USE_MAP":"",Q.matcap?"#define USE_MATCAP":"",Q.envMap?"#define USE_ENVMAP":"",Q.envMap?"#define "+G:"",Q.envMap?"#define "+E:"",Q.envMap?"#define "+U:"",q?"#define CUBEUV_TEXEL_WIDTH "+q.texelWidth:"",q?"#define CUBEUV_TEXEL_HEIGHT "+q.texelHeight:"",q?"#define CUBEUV_MAX_MIP "+q.maxMip+".0":"",Q.lightMap?"#define USE_LIGHTMAP":"",Q.aoMap?"#define USE_AOMAP":"",Q.bumpMap?"#define USE_BUMPMAP":"",Q.normalMap?"#define USE_NORMALMAP":"",Q.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",Q.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",Q.emissiveMap?"#define USE_EMISSIVEMAP":"",Q.anisotropy?"#define USE_ANISOTROPY":"",Q.anisotropyMap?"#define USE_ANISOTROPYMAP":"",Q.clearcoat?"#define USE_CLEARCOAT":"",Q.clearcoatMap?"#define USE_CLEARCOATMAP":"",Q.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",Q.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",Q.dispersion?"#define USE_DISPERSION":"",Q.iridescence?"#define USE_IRIDESCENCE":"",Q.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",Q.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",Q.specularMap?"#define USE_SPECULARMAP":"",Q.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",Q.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",Q.roughnessMap?"#define USE_ROUGHNESSMAP":"",Q.metalnessMap?"#define USE_METALNESSMAP":"",Q.alphaMap?"#define USE_ALPHAMAP":"",Q.alphaTest?"#define USE_ALPHATEST":"",Q.alphaHash?"#define USE_ALPHAHASH":"",Q.sheen?"#define USE_SHEEN":"",Q.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",Q.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",Q.transmission?"#define USE_TRANSMISSION":"",Q.transmissionMap?"#define USE_TRANSMISSIONMAP":"",Q.thicknessMap?"#define USE_THICKNESSMAP":"",Q.vertexTangents&&Q.flatShading===!1?"#define USE_TANGENT":"",Q.vertexColors||Q.instancingColor||Q.batchingColor?"#define USE_COLOR":"",Q.vertexAlphas?"#define USE_COLOR_ALPHA":"",Q.vertexUv1s?"#define USE_UV1":"",Q.vertexUv2s?"#define USE_UV2":"",Q.vertexUv3s?"#define USE_UV3":"",Q.pointsUvs?"#define USE_POINTS_UV":"",Q.gradientMap?"#define USE_GRADIENTMAP":"",Q.flatShading?"#define FLAT_SHADED":"",Q.doubleSided?"#define DOUBLE_SIDED":"",Q.flipSided?"#define FLIP_SIDED":"",Q.shadowMapEnabled?"#define USE_SHADOWMAP":"",Q.shadowMapEnabled?"#define "+K:"",Q.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",Q.numLightProbes>0?"#define USE_LIGHT_PROBES":"",Q.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",Q.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",Q.logarithmicDepthBuffer?"#define USE_LOGDEPTHBUF":"",Q.reverseDepthBuffer?"#define USE_REVERSEDEPTHBUF":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",Q.toneMapping!==0?"#define TONE_MAPPING":"",Q.toneMapping!==0?bJ.tonemapping_pars_fragment:"",Q.toneMapping!==0?X4("toneMapping",Q.toneMapping):"",Q.dithering?"#define DITHERING":"",Q.opaque?"#define OPAQUE":"",bJ.colorspace_pars_fragment,H4("linearToOutputTexel",Q.outputColorSpace),K4(),Q.useDepthPacking?"#define DEPTH_PACKING "+Q.depthPacking:"",`
`].filter(W7).join(`
`);if(X=f8(X),X=n9(X,Q),X=s9(X,Q),H=f8(H),H=n9(H,Q),H=s9(H,Q),X=i9(X),H=i9(H),Q.isRawShaderMaterial!==!0)A=`#version 300 es
`,V=[D,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+V,F=["#define varying in",Q.glslVersion==="300 es"?"":"layout(location = 0) out highp vec4 pc_fragColor;",Q.glslVersion==="300 es"?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+F;let z=A+V+X,_=A+F+H,b=l9(W,W.VERTEX_SHADER,z),L=l9(W,W.FRAGMENT_SHADER,_);if(W.attachShader(O,b),W.attachShader(O,L),Q.index0AttributeName!==void 0)W.bindAttribLocation(O,0,Q.index0AttributeName);else if(Q.morphTargets===!0)W.bindAttribLocation(O,0,"position");W.linkProgram(O);function P(T){if(J.debug.checkShaderErrors){let x=W.getProgramInfoLog(O).trim(),m=W.getShaderInfoLog(b).trim(),u=W.getShaderInfoLog(L).trim(),a=!0,l=!0;if(W.getProgramParameter(O,W.LINK_STATUS)===!1)if(a=!1,typeof J.debug.onShaderError==="function")J.debug.onShaderError(W,O,b,L);else{let t=c9(W,b,"vertex"),g=c9(W,L,"fragment");console.error("THREE.WebGLProgram: Shader Error "+W.getError()+" - VALIDATE_STATUS "+W.getProgramParameter(O,W.VALIDATE_STATUS)+`

Material Name: `+T.name+`
Material Type: `+T.type+`

Program Info Log: `+x+`
`+t+`
`+g)}else if(x!=="")console.warn("THREE.WebGLProgram: Program Info Log:",x);else if(m===""||u==="")l=!1;if(l)T.diagnostics={runnable:a,programLog:x,vertexShader:{log:m,prefix:V},fragmentShader:{log:u,prefix:F}}}W.deleteShader(b),W.deleteShader(L),p=new Y7(W,O),B=q4(W,O)}let p;this.getUniforms=function(){if(p===void 0)P(this);return p};let B;this.getAttributes=function(){if(B===void 0)P(this);return B};let k=Q.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){if(k===!1)k=W.getProgramParameter(O,Q4);return k},this.destroy=function(){Z.releaseStatesOfProgram(this),W.deleteProgram(O),this.program=void 0},this.type=Q.shaderType,this.name=Q.shaderName,this.id=Z4++,this.cacheKey=$,this.usedTimes=1,this.program=O,this.vertexShader=b,this.fragmentShader=L,this}var A4=0;class _${constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(J){let{vertexShader:$,fragmentShader:Q}=J,Z=this._getShaderStage($),W=this._getShaderStage(Q),Y=this._getShaderCacheForMaterial(J);if(Y.has(Z)===!1)Y.add(Z),Z.usedTimes++;if(Y.has(W)===!1)Y.add(W),W.usedTimes++;return this}remove(J){let $=this.materialCache.get(J);for(let Q of $)if(Q.usedTimes--,Q.usedTimes===0)this.shaderCache.delete(Q.code);return this.materialCache.delete(J),this}getVertexShaderID(J){return this._getShaderStage(J.vertexShader).id}getFragmentShaderID(J){return this._getShaderStage(J.fragmentShader).id}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(J){let $=this.materialCache,Q=$.get(J);if(Q===void 0)Q=new Set,$.set(J,Q);return Q}_getShaderStage(J){let $=this.shaderCache,Q=$.get(J);if(Q===void 0)Q=new C$(J),$.set(J,Q);return Q}}class C${constructor(J){this.id=A4++,this.code=J,this.usedTimes=0}}function w4(J,$,Q,Z,W,Y,X){let H=new p8,K=new _$,G=new Set,E=[],U=W.logarithmicDepthBuffer,q=W.vertexTextures,D=W.precision,N={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distanceRGBA",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function O(B){if(G.add(B),B===0)return"uv";return`uv${B}`}function V(B,k,T,x,m){let u=x.fog,a=m.geometry,l=B.isMeshStandardMaterial?x.environment:null,t=(B.isMeshStandardMaterial?Q:$).get(B.envMap||l),g=!!t&&t.mapping===306?t.image.height:null,XJ=N[B.type];if(B.precision!==null){if(D=W.getMaxPrecision(B.precision),D!==B.precision)console.warn("THREE.WebGLProgram.getParameters:",B.precision,"not supported, using",D,"instead.")}let ZJ=a.morphAttributes.position||a.morphAttributes.normal||a.morphAttributes.color,_J=ZJ!==void 0?ZJ.length:0,fJ=0;if(a.morphAttributes.position!==void 0)fJ=1;if(a.morphAttributes.normal!==void 0)fJ=2;if(a.morphAttributes.color!==void 0)fJ=3;let n,e,zJ,kJ;if(XJ){let sJ=b0[XJ];n=sJ.vertexShader,e=sJ.fragmentShader}else n=B.vertexShader,e=B.fragmentShader,K.update(B),zJ=K.getVertexShaderID(B),kJ=K.getFragmentShaderID(B);let YJ=J.getRenderTarget(),d=J.state.buffers.depth.getReversed(),KJ=m.isInstancedMesh===!0,WJ=m.isBatchedMesh===!0,AJ=!!B.map,pJ=!!B.matcap,C=!!t,lJ=!!B.aoMap,CJ=!!B.lightMap,mJ=!!B.bumpMap,GJ=!!B.normalMap,$0=!!B.displacementMap,wJ=!!B.emissiveMap,IJ=!!B.metalnessMap,w=!!B.roughnessMap,R=B.anisotropy>0,j=B.clearcoat>0,o=B.dispersion>0,r=B.iridescence>0,c=B.sheen>0,LJ=B.transmission>0,UJ=R&&!!B.anisotropyMap,DJ=j&&!!B.clearcoatMap,SJ=j&&!!B.clearcoatNormalMap,$J=j&&!!B.clearcoatRoughnessMap,FJ=r&&!!B.iridescenceMap,gJ=r&&!!B.iridescenceThicknessMap,PJ=c&&!!B.sheenColorMap,RJ=c&&!!B.sheenRoughnessMap,yJ=!!B.specularMap,xJ=!!B.specularColorMap,Q0=!!B.specularIntensityMap,I=LJ&&!!B.transmissionMap,JJ=LJ&&!!B.thicknessMap,s=!!B.gradientMap,i=!!B.alphaMap,VJ=B.alphaTest>0,qJ=!!B.alphaHash,hJ=!!B.extensions,W0=0;if(B.toneMapped){if(YJ===null||YJ.isXRRenderTarget===!0)W0=J.toneMapping}let E0={shaderID:XJ,shaderType:B.type,shaderName:B.name,vertexShader:n,fragmentShader:e,defines:B.defines,customVertexShaderID:zJ,customFragmentShaderID:kJ,isRawShaderMaterial:B.isRawShaderMaterial===!0,glslVersion:B.glslVersion,precision:D,batching:WJ,batchingColor:WJ&&m._colorsTexture!==null,instancing:KJ,instancingColor:KJ&&m.instanceColor!==null,instancingMorph:KJ&&m.morphTexture!==null,supportsVertexTextures:q,outputColorSpace:YJ===null?J.outputColorSpace:YJ.isXRRenderTarget===!0?YJ.texture.colorSpace:"srgb-linear",alphaToCoverage:!!B.alphaToCoverage,map:AJ,matcap:pJ,envMap:C,envMapMode:C&&t.mapping,envMapCubeUVHeight:g,aoMap:lJ,lightMap:CJ,bumpMap:mJ,normalMap:GJ,displacementMap:q&&$0,emissiveMap:wJ,normalMapObjectSpace:GJ&&B.normalMapType===1,normalMapTangentSpace:GJ&&B.normalMapType===0,metalnessMap:IJ,roughnessMap:w,anisotropy:R,anisotropyMap:UJ,clearcoat:j,clearcoatMap:DJ,clearcoatNormalMap:SJ,clearcoatRoughnessMap:$J,dispersion:o,iridescence:r,iridescenceMap:FJ,iridescenceThicknessMap:gJ,sheen:c,sheenColorMap:PJ,sheenRoughnessMap:RJ,specularMap:yJ,specularColorMap:xJ,specularIntensityMap:Q0,transmission:LJ,transmissionMap:I,thicknessMap:JJ,gradientMap:s,opaque:B.transparent===!1&&B.blending===1&&B.alphaToCoverage===!1,alphaMap:i,alphaTest:VJ,alphaHash:qJ,combine:B.combine,mapUv:AJ&&O(B.map.channel),aoMapUv:lJ&&O(B.aoMap.channel),lightMapUv:CJ&&O(B.lightMap.channel),bumpMapUv:mJ&&O(B.bumpMap.channel),normalMapUv:GJ&&O(B.normalMap.channel),displacementMapUv:$0&&O(B.displacementMap.channel),emissiveMapUv:wJ&&O(B.emissiveMap.channel),metalnessMapUv:IJ&&O(B.metalnessMap.channel),roughnessMapUv:w&&O(B.roughnessMap.channel),anisotropyMapUv:UJ&&O(B.anisotropyMap.channel),clearcoatMapUv:DJ&&O(B.clearcoatMap.channel),clearcoatNormalMapUv:SJ&&O(B.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:$J&&O(B.clearcoatRoughnessMap.channel),iridescenceMapUv:FJ&&O(B.iridescenceMap.channel),iridescenceThicknessMapUv:gJ&&O(B.iridescenceThicknessMap.channel),sheenColorMapUv:PJ&&O(B.sheenColorMap.channel),sheenRoughnessMapUv:RJ&&O(B.sheenRoughnessMap.channel),specularMapUv:yJ&&O(B.specularMap.channel),specularColorMapUv:xJ&&O(B.specularColorMap.channel),specularIntensityMapUv:Q0&&O(B.specularIntensityMap.channel),transmissionMapUv:I&&O(B.transmissionMap.channel),thicknessMapUv:JJ&&O(B.thicknessMap.channel),alphaMapUv:i&&O(B.alphaMap.channel),vertexTangents:!!a.attributes.tangent&&(GJ||R),vertexColors:B.vertexColors,vertexAlphas:B.vertexColors===!0&&!!a.attributes.color&&a.attributes.color.itemSize===4,pointsUvs:m.isPoints===!0&&!!a.attributes.uv&&(AJ||i),fog:!!u,useFog:B.fog===!0,fogExp2:!!u&&u.isFogExp2,flatShading:B.flatShading===!0,sizeAttenuation:B.sizeAttenuation===!0,logarithmicDepthBuffer:U,reverseDepthBuffer:d,skinning:m.isSkinnedMesh===!0,morphTargets:a.morphAttributes.position!==void 0,morphNormals:a.morphAttributes.normal!==void 0,morphColors:a.morphAttributes.color!==void 0,morphTargetsCount:_J,morphTextureStride:fJ,numDirLights:k.directional.length,numPointLights:k.point.length,numSpotLights:k.spot.length,numSpotLightMaps:k.spotLightMap.length,numRectAreaLights:k.rectArea.length,numHemiLights:k.hemi.length,numDirLightShadows:k.directionalShadowMap.length,numPointLightShadows:k.pointShadowMap.length,numSpotLightShadows:k.spotShadowMap.length,numSpotLightShadowsWithMaps:k.numSpotLightShadowsWithMaps,numLightProbes:k.numLightProbes,numClippingPlanes:X.numPlanes,numClipIntersection:X.numIntersection,dithering:B.dithering,shadowMapEnabled:J.shadowMap.enabled&&T.length>0,shadowMapType:J.shadowMap.type,toneMapping:W0,decodeVideoTexture:AJ&&B.map.isVideoTexture===!0&&dJ.getTransfer(B.map.colorSpace)==="srgb",decodeVideoTextureEmissive:wJ&&B.emissiveMap.isVideoTexture===!0&&dJ.getTransfer(B.emissiveMap.colorSpace)==="srgb",premultipliedAlpha:B.premultipliedAlpha,doubleSided:B.side===2,flipSided:B.side===1,useDepthPacking:B.depthPacking>=0,depthPacking:B.depthPacking||0,index0AttributeName:B.index0AttributeName,extensionClipCullDistance:hJ&&B.extensions.clipCullDistance===!0&&Z.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(hJ&&B.extensions.multiDraw===!0||WJ)&&Z.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:Z.has("KHR_parallel_shader_compile"),customProgramCacheKey:B.customProgramCacheKey()};return E0.vertexUv1s=G.has(1),E0.vertexUv2s=G.has(2),E0.vertexUv3s=G.has(3),G.clear(),E0}function F(B){let k=[];if(B.shaderID)k.push(B.shaderID);else k.push(B.customVertexShaderID),k.push(B.customFragmentShaderID);if(B.defines!==void 0)for(let T in B.defines)k.push(T),k.push(B.defines[T]);if(B.isRawShaderMaterial===!1)A(k,B),z(k,B),k.push(J.outputColorSpace);return k.push(B.customProgramCacheKey),k.join()}function A(B,k){B.push(k.precision),B.push(k.outputColorSpace),B.push(k.envMapMode),B.push(k.envMapCubeUVHeight),B.push(k.mapUv),B.push(k.alphaMapUv),B.push(k.lightMapUv),B.push(k.aoMapUv),B.push(k.bumpMapUv),B.push(k.normalMapUv),B.push(k.displacementMapUv),B.push(k.emissiveMapUv),B.push(k.metalnessMapUv),B.push(k.roughnessMapUv),B.push(k.anisotropyMapUv),B.push(k.clearcoatMapUv),B.push(k.clearcoatNormalMapUv),B.push(k.clearcoatRoughnessMapUv),B.push(k.iridescenceMapUv),B.push(k.iridescenceThicknessMapUv),B.push(k.sheenColorMapUv),B.push(k.sheenRoughnessMapUv),B.push(k.specularMapUv),B.push(k.specularColorMapUv),B.push(k.specularIntensityMapUv),B.push(k.transmissionMapUv),B.push(k.thicknessMapUv),B.push(k.combine),B.push(k.fogExp2),B.push(k.sizeAttenuation),B.push(k.morphTargetsCount),B.push(k.morphAttributeCount),B.push(k.numDirLights),B.push(k.numPointLights),B.push(k.numSpotLights),B.push(k.numSpotLightMaps),B.push(k.numHemiLights),B.push(k.numRectAreaLights),B.push(k.numDirLightShadows),B.push(k.numPointLightShadows),B.push(k.numSpotLightShadows),B.push(k.numSpotLightShadowsWithMaps),B.push(k.numLightProbes),B.push(k.shadowMapType),B.push(k.toneMapping),B.push(k.numClippingPlanes),B.push(k.numClipIntersection),B.push(k.depthPacking)}function z(B,k){if(H.disableAll(),k.supportsVertexTextures)H.enable(0);if(k.instancing)H.enable(1);if(k.instancingColor)H.enable(2);if(k.instancingMorph)H.enable(3);if(k.matcap)H.enable(4);if(k.envMap)H.enable(5);if(k.normalMapObjectSpace)H.enable(6);if(k.normalMapTangentSpace)H.enable(7);if(k.clearcoat)H.enable(8);if(k.iridescence)H.enable(9);if(k.alphaTest)H.enable(10);if(k.vertexColors)H.enable(11);if(k.vertexAlphas)H.enable(12);if(k.vertexUv1s)H.enable(13);if(k.vertexUv2s)H.enable(14);if(k.vertexUv3s)H.enable(15);if(k.vertexTangents)H.enable(16);if(k.anisotropy)H.enable(17);if(k.alphaHash)H.enable(18);if(k.batching)H.enable(19);if(k.dispersion)H.enable(20);if(k.batchingColor)H.enable(21);if(B.push(H.mask),H.disableAll(),k.fog)H.enable(0);if(k.useFog)H.enable(1);if(k.flatShading)H.enable(2);if(k.logarithmicDepthBuffer)H.enable(3);if(k.reverseDepthBuffer)H.enable(4);if(k.skinning)H.enable(5);if(k.morphTargets)H.enable(6);if(k.morphNormals)H.enable(7);if(k.morphColors)H.enable(8);if(k.premultipliedAlpha)H.enable(9);if(k.shadowMapEnabled)H.enable(10);if(k.doubleSided)H.enable(11);if(k.flipSided)H.enable(12);if(k.useDepthPacking)H.enable(13);if(k.dithering)H.enable(14);if(k.transmission)H.enable(15);if(k.sheen)H.enable(16);if(k.opaque)H.enable(17);if(k.pointsUvs)H.enable(18);if(k.decodeVideoTexture)H.enable(19);if(k.decodeVideoTextureEmissive)H.enable(20);if(k.alphaToCoverage)H.enable(21);B.push(H.mask)}function _(B){let k=N[B.type],T;if(k){let x=b0[k];T=F5.clone(x.uniforms)}else T=B.uniforms;return T}function b(B,k){let T;for(let x=0,m=E.length;x<m;x++){let u=E[x];if(u.cacheKey===k){T=u,++T.usedTimes;break}}if(T===void 0)T=new k4(J,k,B,Y),E.push(T);return T}function L(B){if(--B.usedTimes===0){let k=E.indexOf(B);E[k]=E[E.length-1],E.pop(),B.destroy()}}function P(B){K.remove(B)}function p(){K.dispose()}return{getParameters:V,getProgramCacheKey:F,getUniforms:_,acquireProgram:b,releaseProgram:L,releaseShaderCache:P,programs:E,dispose:p}}function L4(){let J=new WeakMap;function $(X){return J.has(X)}function Q(X){let H=J.get(X);if(H===void 0)H={},J.set(X,H);return H}function Z(X){J.delete(X)}function W(X,H,K){J.get(X)[H]=K}function Y(){J=new WeakMap}return{has:$,get:Q,remove:Z,update:W,dispose:Y}}function _4(J,$){if(J.groupOrder!==$.groupOrder)return J.groupOrder-$.groupOrder;else if(J.renderOrder!==$.renderOrder)return J.renderOrder-$.renderOrder;else if(J.material.id!==$.material.id)return J.material.id-$.material.id;else if(J.z!==$.z)return J.z-$.z;else return J.id-$.id}function a9(J,$){if(J.groupOrder!==$.groupOrder)return J.groupOrder-$.groupOrder;else if(J.renderOrder!==$.renderOrder)return J.renderOrder-$.renderOrder;else if(J.z!==$.z)return $.z-J.z;else return J.id-$.id}function r9(){let J=[],$=0,Q=[],Z=[],W=[];function Y(){$=0,Q.length=0,Z.length=0,W.length=0}function X(U,q,D,N,O,V){let F=J[$];if(F===void 0)F={id:U.id,object:U,geometry:q,material:D,groupOrder:N,renderOrder:U.renderOrder,z:O,group:V},J[$]=F;else F.id=U.id,F.object=U,F.geometry=q,F.material=D,F.groupOrder=N,F.renderOrder=U.renderOrder,F.z=O,F.group=V;return $++,F}function H(U,q,D,N,O,V){let F=X(U,q,D,N,O,V);if(D.transmission>0)Z.push(F);else if(D.transparent===!0)W.push(F);else Q.push(F)}function K(U,q,D,N,O,V){let F=X(U,q,D,N,O,V);if(D.transmission>0)Z.unshift(F);else if(D.transparent===!0)W.unshift(F);else Q.unshift(F)}function G(U,q){if(Q.length>1)Q.sort(U||_4);if(Z.length>1)Z.sort(q||a9);if(W.length>1)W.sort(q||a9)}function E(){for(let U=$,q=J.length;U<q;U++){let D=J[U];if(D.id===null)break;D.id=null,D.object=null,D.geometry=null,D.material=null,D.group=null}}return{opaque:Q,transmissive:Z,transparent:W,init:Y,push:H,unshift:K,finish:E,sort:G}}function C4(){let J=new WeakMap;function $(Z,W){let Y=J.get(Z),X;if(Y===void 0)X=new r9,J.set(Z,[X]);else if(W>=Y.length)X=new r9,Y.push(X);else X=Y[W];return X}function Q(){J=new WeakMap}return{get:$,dispose:Q}}function P4(){let J={};return{get:function($){if(J[$.id]!==void 0)return J[$.id];let Q;switch($.type){case"DirectionalLight":Q={direction:new v,color:new nJ};break;case"SpotLight":Q={position:new v,direction:new v,color:new nJ,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":Q={position:new v,color:new nJ,distance:0,decay:0};break;case"HemisphereLight":Q={direction:new v,skyColor:new nJ,groundColor:new nJ};break;case"RectAreaLight":Q={color:new nJ,position:new v,halfWidth:new v,halfHeight:new v};break}return J[$.id]=Q,Q}}}function T4(){let J={};return{get:function($){if(J[$.id]!==void 0)return J[$.id];let Q;switch($.type){case"DirectionalLight":Q={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new uJ};break;case"SpotLight":Q={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new uJ};break;case"PointLight":Q={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new uJ,shadowCameraNear:1,shadowCameraFar:1000};break}return J[$.id]=Q,Q}}}var I4=0;function S4(J,$){return($.castShadow?2:0)-(J.castShadow?2:0)+($.map?1:0)-(J.map?1:0)}function y4(J){let $=new P4,Q=T4(),Z={version:0,hash:{directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let G=0;G<9;G++)Z.probe.push(new v);let W=new v,Y=new Z0,X=new Z0;function H(G){let E=0,U=0,q=0;for(let B=0;B<9;B++)Z.probe[B].set(0,0,0);let D=0,N=0,O=0,V=0,F=0,A=0,z=0,_=0,b=0,L=0,P=0;G.sort(S4);for(let B=0,k=G.length;B<k;B++){let T=G[B],x=T.color,m=T.intensity,u=T.distance,a=T.shadow&&T.shadow.map?T.shadow.map.texture:null;if(T.isAmbientLight)E+=x.r*m,U+=x.g*m,q+=x.b*m;else if(T.isLightProbe){for(let l=0;l<9;l++)Z.probe[l].addScaledVector(T.sh.coefficients[l],m);P++}else if(T.isDirectionalLight){let l=$.get(T);if(l.color.copy(T.color).multiplyScalar(T.intensity),T.castShadow){let t=T.shadow,g=Q.get(T);g.shadowIntensity=t.intensity,g.shadowBias=t.bias,g.shadowNormalBias=t.normalBias,g.shadowRadius=t.radius,g.shadowMapSize=t.mapSize,Z.directionalShadow[D]=g,Z.directionalShadowMap[D]=a,Z.directionalShadowMatrix[D]=T.shadow.matrix,A++}Z.directional[D]=l,D++}else if(T.isSpotLight){let l=$.get(T);l.position.setFromMatrixPosition(T.matrixWorld),l.color.copy(x).multiplyScalar(m),l.distance=u,l.coneCos=Math.cos(T.angle),l.penumbraCos=Math.cos(T.angle*(1-T.penumbra)),l.decay=T.decay,Z.spot[O]=l;let t=T.shadow;if(T.map){if(Z.spotLightMap[b]=T.map,b++,t.updateMatrices(T),T.castShadow)L++}if(Z.spotLightMatrix[O]=t.matrix,T.castShadow){let g=Q.get(T);g.shadowIntensity=t.intensity,g.shadowBias=t.bias,g.shadowNormalBias=t.normalBias,g.shadowRadius=t.radius,g.shadowMapSize=t.mapSize,Z.spotShadow[O]=g,Z.spotShadowMap[O]=a,_++}O++}else if(T.isRectAreaLight){let l=$.get(T);l.color.copy(x).multiplyScalar(m),l.halfWidth.set(T.width*0.5,0,0),l.halfHeight.set(0,T.height*0.5,0),Z.rectArea[V]=l,V++}else if(T.isPointLight){let l=$.get(T);if(l.color.copy(T.color).multiplyScalar(T.intensity),l.distance=T.distance,l.decay=T.decay,T.castShadow){let t=T.shadow,g=Q.get(T);g.shadowIntensity=t.intensity,g.shadowBias=t.bias,g.shadowNormalBias=t.normalBias,g.shadowRadius=t.radius,g.shadowMapSize=t.mapSize,g.shadowCameraNear=t.camera.near,g.shadowCameraFar=t.camera.far,Z.pointShadow[N]=g,Z.pointShadowMap[N]=a,Z.pointShadowMatrix[N]=T.shadow.matrix,z++}Z.point[N]=l,N++}else if(T.isHemisphereLight){let l=$.get(T);l.skyColor.copy(T.color).multiplyScalar(m),l.groundColor.copy(T.groundColor).multiplyScalar(m),Z.hemi[F]=l,F++}}if(V>0)if(J.has("OES_texture_float_linear")===!0)Z.rectAreaLTC1=HJ.LTC_FLOAT_1,Z.rectAreaLTC2=HJ.LTC_FLOAT_2;else Z.rectAreaLTC1=HJ.LTC_HALF_1,Z.rectAreaLTC2=HJ.LTC_HALF_2;Z.ambient[0]=E,Z.ambient[1]=U,Z.ambient[2]=q;let p=Z.hash;if(p.directionalLength!==D||p.pointLength!==N||p.spotLength!==O||p.rectAreaLength!==V||p.hemiLength!==F||p.numDirectionalShadows!==A||p.numPointShadows!==z||p.numSpotShadows!==_||p.numSpotMaps!==b||p.numLightProbes!==P)Z.directional.length=D,Z.spot.length=O,Z.rectArea.length=V,Z.point.length=N,Z.hemi.length=F,Z.directionalShadow.length=A,Z.directionalShadowMap.length=A,Z.pointShadow.length=z,Z.pointShadowMap.length=z,Z.spotShadow.length=_,Z.spotShadowMap.length=_,Z.directionalShadowMatrix.length=A,Z.pointShadowMatrix.length=z,Z.spotLightMatrix.length=_+b-L,Z.spotLightMap.length=b,Z.numSpotLightShadowsWithMaps=L,Z.numLightProbes=P,p.directionalLength=D,p.pointLength=N,p.spotLength=O,p.rectAreaLength=V,p.hemiLength=F,p.numDirectionalShadows=A,p.numPointShadows=z,p.numSpotShadows=_,p.numSpotMaps=b,p.numLightProbes=P,Z.version=I4++}function K(G,E){let U=0,q=0,D=0,N=0,O=0,V=E.matrixWorldInverse;for(let F=0,A=G.length;F<A;F++){let z=G[F];if(z.isDirectionalLight){let _=Z.directional[U];_.direction.setFromMatrixPosition(z.matrixWorld),W.setFromMatrixPosition(z.target.matrixWorld),_.direction.sub(W),_.direction.transformDirection(V),U++}else if(z.isSpotLight){let _=Z.spot[D];_.position.setFromMatrixPosition(z.matrixWorld),_.position.applyMatrix4(V),_.direction.setFromMatrixPosition(z.matrixWorld),W.setFromMatrixPosition(z.target.matrixWorld),_.direction.sub(W),_.direction.transformDirection(V),D++}else if(z.isRectAreaLight){let _=Z.rectArea[N];_.position.setFromMatrixPosition(z.matrixWorld),_.position.applyMatrix4(V),X.identity(),Y.copy(z.matrixWorld),Y.premultiply(V),X.extractRotation(Y),_.halfWidth.set(z.width*0.5,0,0),_.halfHeight.set(0,z.height*0.5,0),_.halfWidth.applyMatrix4(X),_.halfHeight.applyMatrix4(X),N++}else if(z.isPointLight){let _=Z.point[q];_.position.setFromMatrixPosition(z.matrixWorld),_.position.applyMatrix4(V),q++}else if(z.isHemisphereLight){let _=Z.hemi[O];_.direction.setFromMatrixPosition(z.matrixWorld),_.direction.transformDirection(V),O++}}}return{setup:H,setupView:K,state:Z}}function t9(J){let $=new y4(J),Q=[],Z=[];function W(E){G.camera=E,Q.length=0,Z.length=0}function Y(E){Q.push(E)}function X(E){Z.push(E)}function H(){$.setup(Q)}function K(E){$.setupView(Q,E)}let G={lightsArray:Q,shadowsArray:Z,camera:null,lights:$,transmissionRenderTarget:{}};return{init:W,state:G,setupLights:H,setupLightsView:K,pushLight:Y,pushShadow:X}}function v4(J){let $=new WeakMap;function Q(W,Y=0){let X=$.get(W),H;if(X===void 0)H=new t9(J),$.set(W,[H]);else if(Y>=X.length)H=new t9(J),X.push(H);else H=X[Y];return H}function Z(){$=new WeakMap}return{get:Q,dispose:Z}}class P$ extends K6{static get type(){return"MeshDepthMaterial"}constructor(J){super();this.isMeshDepthMaterial=!0,this.depthPacking=3200,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(J)}copy(J){return super.copy(J),this.depthPacking=J.depthPacking,this.map=J.map,this.alphaMap=J.alphaMap,this.displacementMap=J.displacementMap,this.displacementScale=J.displacementScale,this.displacementBias=J.displacementBias,this.wireframe=J.wireframe,this.wireframeLinewidth=J.wireframeLinewidth,this}}class T$ extends K6{static get type(){return"MeshDistanceMaterial"}constructor(J){super();this.isMeshDistanceMaterial=!0,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(J)}copy(J){return super.copy(J),this.map=J.map,this.alphaMap=J.alphaMap,this.displacementMap=J.displacementMap,this.displacementScale=J.displacementScale,this.displacementBias=J.displacementBias,this}}var j4=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,f4=`uniform sampler2D shadow_pass;
uniform vec2 resolution;
uniform float radius;
#include <packing>
void main() {
	const float samples = float( VSM_SAMPLES );
	float mean = 0.0;
	float squared_mean = 0.0;
	float uvStride = samples <= 1.0 ? 0.0 : 2.0 / ( samples - 1.0 );
	float uvStart = samples <= 1.0 ? 0.0 : - 1.0;
	for ( float i = 0.0; i < samples; i ++ ) {
		float uvOffset = uvStart + i * uvStride;
		#ifdef HORIZONTAL_PASS
			vec2 distribution = unpackRGBATo2Half( texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( uvOffset, 0.0 ) * radius ) / resolution ) );
			mean += distribution.x;
			squared_mean += distribution.y * distribution.y + distribution.x * distribution.x;
		#else
			float depth = unpackRGBAToDepth( texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( 0.0, uvOffset ) * radius ) / resolution ) );
			mean += depth;
			squared_mean += depth * depth;
		#endif
	}
	mean = mean / samples;
	squared_mean = squared_mean / samples;
	float std_dev = sqrt( squared_mean - mean * mean );
	gl_FragColor = pack2HalfToRGBA( vec2( mean, std_dev ) );
}`;function h4(J,$,Q){let Z=new d8,W=new uJ,Y=new uJ,X=new H0,H=new P$({depthPacking:3201}),K=new T$,G={},E=Q.maxTextureSize,U={[0]:1,[1]:0,[2]:2},q=new a0({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new uJ},radius:{value:4}},vertexShader:j4,fragmentShader:f4}),D=q.clone();D.defines.HORIZONTAL_PASS=1;let N=new V0;N.setAttribute("position",new I0(new Float32Array([-1,-1,0.5,3,-1,0.5,-1,3,0.5]),3));let O=new T0(N,q),V=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=1;let F=this.type;this.render=function(L,P,p){if(V.enabled===!1)return;if(V.autoUpdate===!1&&V.needsUpdate===!1)return;if(L.length===0)return;let B=J.getRenderTarget(),k=J.getActiveCubeFace(),T=J.getActiveMipmapLevel(),x=J.state;x.setBlending(0),x.buffers.color.setClear(1,1,1,1),x.buffers.depth.setTest(!0),x.setScissorTest(!1);let m=F!==3&&this.type===3,u=F===3&&this.type!==3;for(let a=0,l=L.length;a<l;a++){let t=L[a],g=t.shadow;if(g===void 0){console.warn("THREE.WebGLShadowMap:",t,"has no shadow.");continue}if(g.autoUpdate===!1&&g.needsUpdate===!1)continue;W.copy(g.mapSize);let XJ=g.getFrameExtents();if(W.multiply(XJ),Y.copy(g.mapSize),W.x>E||W.y>E){if(W.x>E)Y.x=Math.floor(E/XJ.x),W.x=Y.x*XJ.x,g.mapSize.x=Y.x;if(W.y>E)Y.y=Math.floor(E/XJ.y),W.y=Y.y*XJ.y,g.mapSize.y=Y.y}if(g.map===null||m===!0||u===!0){let _J=this.type!==3?{minFilter:1003,magFilter:1003}:{};if(g.map!==null)g.map.dispose();g.map=new X6(W.x,W.y,_J),g.map.texture.name=t.name+".shadowMap",g.camera.updateProjectionMatrix()}J.setRenderTarget(g.map),J.clear();let ZJ=g.getViewportCount();for(let _J=0;_J<ZJ;_J++){let fJ=g.getViewport(_J);X.set(Y.x*fJ.x,Y.y*fJ.y,Y.x*fJ.z,Y.y*fJ.w),x.viewport(X),g.updateMatrices(t,_J),Z=g.getFrustum(),_(P,p,g.camera,t,this.type)}if(g.isPointLightShadow!==!0&&this.type===3)A(g,p);g.needsUpdate=!1}F=this.type,V.needsUpdate=!1,J.setRenderTarget(B,k,T)};function A(L,P){let p=$.update(O);if(q.defines.VSM_SAMPLES!==L.blurSamples)q.defines.VSM_SAMPLES=L.blurSamples,D.defines.VSM_SAMPLES=L.blurSamples,q.needsUpdate=!0,D.needsUpdate=!0;if(L.mapPass===null)L.mapPass=new X6(W.x,W.y);q.uniforms.shadow_pass.value=L.map.texture,q.uniforms.resolution.value=L.mapSize,q.uniforms.radius.value=L.radius,J.setRenderTarget(L.mapPass),J.clear(),J.renderBufferDirect(P,null,p,q,O,null),D.uniforms.shadow_pass.value=L.mapPass.texture,D.uniforms.resolution.value=L.mapSize,D.uniforms.radius.value=L.radius,J.setRenderTarget(L.map),J.clear(),J.renderBufferDirect(P,null,p,D,O,null)}function z(L,P,p,B){let k=null,T=p.isPointLight===!0?L.customDistanceMaterial:L.customDepthMaterial;if(T!==void 0)k=T;else if(k=p.isPointLight===!0?K:H,J.localClippingEnabled&&P.clipShadows===!0&&Array.isArray(P.clippingPlanes)&&P.clippingPlanes.length!==0||P.displacementMap&&P.displacementScale!==0||P.alphaMap&&P.alphaTest>0||P.map&&P.alphaTest>0){let x=k.uuid,m=P.uuid,u=G[x];if(u===void 0)u={},G[x]=u;let a=u[m];if(a===void 0)a=k.clone(),u[m]=a,P.addEventListener("dispose",b);k=a}if(k.visible=P.visible,k.wireframe=P.wireframe,B===3)k.side=P.shadowSide!==null?P.shadowSide:P.side;else k.side=P.shadowSide!==null?P.shadowSide:U[P.side];if(k.alphaMap=P.alphaMap,k.alphaTest=P.alphaTest,k.map=P.map,k.clipShadows=P.clipShadows,k.clippingPlanes=P.clippingPlanes,k.clipIntersection=P.clipIntersection,k.displacementMap=P.displacementMap,k.displacementScale=P.displacementScale,k.displacementBias=P.displacementBias,k.wireframeLinewidth=P.wireframeLinewidth,k.linewidth=P.linewidth,p.isPointLight===!0&&k.isMeshDistanceMaterial===!0){let x=J.properties.get(k);x.light=p}return k}function _(L,P,p,B,k){if(L.visible===!1)return;if(L.layers.test(P.layers)&&(L.isMesh||L.isLine||L.isPoints)){if((L.castShadow||L.receiveShadow&&k===3)&&(!L.frustumCulled||Z.intersectsObject(L))){L.modelViewMatrix.multiplyMatrices(p.matrixWorldInverse,L.matrixWorld);let m=$.update(L),u=L.material;if(Array.isArray(u)){let a=m.groups;for(let l=0,t=a.length;l<t;l++){let g=a[l],XJ=u[g.materialIndex];if(XJ&&XJ.visible){let ZJ=z(L,XJ,B,k);L.onBeforeShadow(J,L,P,p,m,ZJ,g),J.renderBufferDirect(p,null,m,ZJ,L,g),L.onAfterShadow(J,L,P,p,m,ZJ,g)}}}else if(u.visible){let a=z(L,u,B,k);L.onBeforeShadow(J,L,P,p,m,a,null),J.renderBufferDirect(p,null,m,a,L,null),L.onAfterShadow(J,L,P,p,m,a,null)}}}let x=L.children;for(let m=0,u=x.length;m<u;m++)_(x[m],P,p,B,k)}function b(L){L.target.removeEventListener("dispose",b);for(let p in G){let B=G[p],k=L.target.uuid;if(k in B)B[k].dispose(),delete B[k]}}}var b4={[0]:1,[2]:6,[4]:7,[3]:5,[1]:0,[6]:2,[7]:4,[5]:3};function x4(J,$){function Q(){let I=!1,JJ=new H0,s=null,i=new H0(0,0,0,0);return{setMask:function(VJ){if(s!==VJ&&!I)J.colorMask(VJ,VJ,VJ,VJ),s=VJ},setLocked:function(VJ){I=VJ},setClear:function(VJ,qJ,hJ,W0,E0){if(E0===!0)VJ*=W0,qJ*=W0,hJ*=W0;if(JJ.set(VJ,qJ,hJ,W0),i.equals(JJ)===!1)J.clearColor(VJ,qJ,hJ,W0),i.copy(JJ)},reset:function(){I=!1,s=null,i.set(-1,0,0,0)}}}function Z(){let I=!1,JJ=!1,s=null,i=null,VJ=null;return{setReversed:function(qJ){if(JJ!==qJ){let hJ=$.get("EXT_clip_control");if(JJ)hJ.clipControlEXT(hJ.LOWER_LEFT_EXT,hJ.ZERO_TO_ONE_EXT);else hJ.clipControlEXT(hJ.LOWER_LEFT_EXT,hJ.NEGATIVE_ONE_TO_ONE_EXT);let W0=VJ;VJ=null,this.setClear(W0)}JJ=qJ},getReversed:function(){return JJ},setTest:function(qJ){if(qJ)YJ(J.DEPTH_TEST);else d(J.DEPTH_TEST)},setMask:function(qJ){if(s!==qJ&&!I)J.depthMask(qJ),s=qJ},setFunc:function(qJ){if(JJ)qJ=b4[qJ];if(i!==qJ){switch(qJ){case 0:J.depthFunc(J.NEVER);break;case 1:J.depthFunc(J.ALWAYS);break;case 2:J.depthFunc(J.LESS);break;case 3:J.depthFunc(J.LEQUAL);break;case 4:J.depthFunc(J.EQUAL);break;case 5:J.depthFunc(J.GEQUAL);break;case 6:J.depthFunc(J.GREATER);break;case 7:J.depthFunc(J.NOTEQUAL);break;default:J.depthFunc(J.LEQUAL)}i=qJ}},setLocked:function(qJ){I=qJ},setClear:function(qJ){if(VJ!==qJ){if(JJ)qJ=1-qJ;J.clearDepth(qJ),VJ=qJ}},reset:function(){I=!1,s=null,i=null,VJ=null,JJ=!1}}}function W(){let I=!1,JJ=null,s=null,i=null,VJ=null,qJ=null,hJ=null,W0=null,E0=null;return{setTest:function(sJ){if(!I)if(sJ)YJ(J.STENCIL_TEST);else d(J.STENCIL_TEST)},setMask:function(sJ){if(JJ!==sJ&&!I)J.stencilMask(sJ),JJ=sJ},setFunc:function(sJ,g0,f0){if(s!==sJ||i!==g0||VJ!==f0)J.stencilFunc(sJ,g0,f0),s=sJ,i=g0,VJ=f0},setOp:function(sJ,g0,f0){if(qJ!==sJ||hJ!==g0||W0!==f0)J.stencilOp(sJ,g0,f0),qJ=sJ,hJ=g0,W0=f0},setLocked:function(sJ){I=sJ},setClear:function(sJ){if(E0!==sJ)J.clearStencil(sJ),E0=sJ},reset:function(){I=!1,JJ=null,s=null,i=null,VJ=null,qJ=null,hJ=null,W0=null,E0=null}}}let Y=new Q,X=new Z,H=new W,K=new WeakMap,G=new WeakMap,E={},U={},q=new WeakMap,D=[],N=null,O=!1,V=null,F=null,A=null,z=null,_=null,b=null,L=null,P=new nJ(0,0,0),p=0,B=!1,k=null,T=null,x=null,m=null,u=null,a=J.getParameter(J.MAX_COMBINED_TEXTURE_IMAGE_UNITS),l=!1,t=0,g=J.getParameter(J.VERSION);if(g.indexOf("WebGL")!==-1)t=parseFloat(/^WebGL (\d)/.exec(g)[1]),l=t>=1;else if(g.indexOf("OpenGL ES")!==-1)t=parseFloat(/^OpenGL ES (\d)/.exec(g)[1]),l=t>=2;let XJ=null,ZJ={},_J=J.getParameter(J.SCISSOR_BOX),fJ=J.getParameter(J.VIEWPORT),n=new H0().fromArray(_J),e=new H0().fromArray(fJ);function zJ(I,JJ,s,i){let VJ=new Uint8Array(4),qJ=J.createTexture();J.bindTexture(I,qJ),J.texParameteri(I,J.TEXTURE_MIN_FILTER,J.NEAREST),J.texParameteri(I,J.TEXTURE_MAG_FILTER,J.NEAREST);for(let hJ=0;hJ<s;hJ++)if(I===J.TEXTURE_3D||I===J.TEXTURE_2D_ARRAY)J.texImage3D(JJ,0,J.RGBA,1,1,i,0,J.RGBA,J.UNSIGNED_BYTE,VJ);else J.texImage2D(JJ+hJ,0,J.RGBA,1,1,0,J.RGBA,J.UNSIGNED_BYTE,VJ);return qJ}let kJ={};kJ[J.TEXTURE_2D]=zJ(J.TEXTURE_2D,J.TEXTURE_2D,1),kJ[J.TEXTURE_CUBE_MAP]=zJ(J.TEXTURE_CUBE_MAP,J.TEXTURE_CUBE_MAP_POSITIVE_X,6),kJ[J.TEXTURE_2D_ARRAY]=zJ(J.TEXTURE_2D_ARRAY,J.TEXTURE_2D_ARRAY,1,1),kJ[J.TEXTURE_3D]=zJ(J.TEXTURE_3D,J.TEXTURE_3D,1,1),Y.setClear(0,0,0,1),X.setClear(1),H.setClear(0),YJ(J.DEPTH_TEST),X.setFunc(3),mJ(!1),GJ(1),YJ(J.CULL_FACE),lJ(0);function YJ(I){if(E[I]!==!0)J.enable(I),E[I]=!0}function d(I){if(E[I]!==!1)J.disable(I),E[I]=!1}function KJ(I,JJ){if(U[I]!==JJ){if(J.bindFramebuffer(I,JJ),U[I]=JJ,I===J.DRAW_FRAMEBUFFER)U[J.FRAMEBUFFER]=JJ;if(I===J.FRAMEBUFFER)U[J.DRAW_FRAMEBUFFER]=JJ;return!0}return!1}function WJ(I,JJ){let s=D,i=!1;if(I){if(s=q.get(JJ),s===void 0)s=[],q.set(JJ,s);let VJ=I.textures;if(s.length!==VJ.length||s[0]!==J.COLOR_ATTACHMENT0){for(let qJ=0,hJ=VJ.length;qJ<hJ;qJ++)s[qJ]=J.COLOR_ATTACHMENT0+qJ;s.length=VJ.length,i=!0}}else if(s[0]!==J.BACK)s[0]=J.BACK,i=!0;if(i)J.drawBuffers(s)}function AJ(I){if(N!==I)return J.useProgram(I),N=I,!0;return!1}let pJ={[100]:J.FUNC_ADD,[101]:J.FUNC_SUBTRACT,[102]:J.FUNC_REVERSE_SUBTRACT};pJ[103]=J.MIN,pJ[104]=J.MAX;let C={[200]:J.ZERO,[201]:J.ONE,[202]:J.SRC_COLOR,[204]:J.SRC_ALPHA,[210]:J.SRC_ALPHA_SATURATE,[208]:J.DST_COLOR,[206]:J.DST_ALPHA,[203]:J.ONE_MINUS_SRC_COLOR,[205]:J.ONE_MINUS_SRC_ALPHA,[209]:J.ONE_MINUS_DST_COLOR,[207]:J.ONE_MINUS_DST_ALPHA,[211]:J.CONSTANT_COLOR,[212]:J.ONE_MINUS_CONSTANT_COLOR,[213]:J.CONSTANT_ALPHA,[214]:J.ONE_MINUS_CONSTANT_ALPHA};function lJ(I,JJ,s,i,VJ,qJ,hJ,W0,E0,sJ){if(I===0){if(O===!0)d(J.BLEND),O=!1;return}if(O===!1)YJ(J.BLEND),O=!0;if(I!==5){if(I!==V||sJ!==B){if(F!==100||_!==100)J.blendEquation(J.FUNC_ADD),F=100,_=100;if(sJ)switch(I){case 1:J.blendFuncSeparate(J.ONE,J.ONE_MINUS_SRC_ALPHA,J.ONE,J.ONE_MINUS_SRC_ALPHA);break;case 2:J.blendFunc(J.ONE,J.ONE);break;case 3:J.blendFuncSeparate(J.ZERO,J.ONE_MINUS_SRC_COLOR,J.ZERO,J.ONE);break;case 4:J.blendFuncSeparate(J.ZERO,J.SRC_COLOR,J.ZERO,J.SRC_ALPHA);break;default:console.error("THREE.WebGLState: Invalid blending: ",I);break}else switch(I){case 1:J.blendFuncSeparate(J.SRC_ALPHA,J.ONE_MINUS_SRC_ALPHA,J.ONE,J.ONE_MINUS_SRC_ALPHA);break;case 2:J.blendFunc(J.SRC_ALPHA,J.ONE);break;case 3:J.blendFuncSeparate(J.ZERO,J.ONE_MINUS_SRC_COLOR,J.ZERO,J.ONE);break;case 4:J.blendFunc(J.ZERO,J.SRC_COLOR);break;default:console.error("THREE.WebGLState: Invalid blending: ",I);break}A=null,z=null,b=null,L=null,P.set(0,0,0),p=0,V=I,B=sJ}return}if(VJ=VJ||JJ,qJ=qJ||s,hJ=hJ||i,JJ!==F||VJ!==_)J.blendEquationSeparate(pJ[JJ],pJ[VJ]),F=JJ,_=VJ;if(s!==A||i!==z||qJ!==b||hJ!==L)J.blendFuncSeparate(C[s],C[i],C[qJ],C[hJ]),A=s,z=i,b=qJ,L=hJ;if(W0.equals(P)===!1||E0!==p)J.blendColor(W0.r,W0.g,W0.b,E0),P.copy(W0),p=E0;V=I,B=!1}function CJ(I,JJ){I.side===2?d(J.CULL_FACE):YJ(J.CULL_FACE);let s=I.side===1;if(JJ)s=!s;mJ(s),I.blending===1&&I.transparent===!1?lJ(0):lJ(I.blending,I.blendEquation,I.blendSrc,I.blendDst,I.blendEquationAlpha,I.blendSrcAlpha,I.blendDstAlpha,I.blendColor,I.blendAlpha,I.premultipliedAlpha),X.setFunc(I.depthFunc),X.setTest(I.depthTest),X.setMask(I.depthWrite),Y.setMask(I.colorWrite);let i=I.stencilWrite;if(H.setTest(i),i)H.setMask(I.stencilWriteMask),H.setFunc(I.stencilFunc,I.stencilRef,I.stencilFuncMask),H.setOp(I.stencilFail,I.stencilZFail,I.stencilZPass);wJ(I.polygonOffset,I.polygonOffsetFactor,I.polygonOffsetUnits),I.alphaToCoverage===!0?YJ(J.SAMPLE_ALPHA_TO_COVERAGE):d(J.SAMPLE_ALPHA_TO_COVERAGE)}function mJ(I){if(k!==I){if(I)J.frontFace(J.CW);else J.frontFace(J.CCW);k=I}}function GJ(I){if(I!==0){if(YJ(J.CULL_FACE),I!==T)if(I===1)J.cullFace(J.BACK);else if(I===2)J.cullFace(J.FRONT);else J.cullFace(J.FRONT_AND_BACK)}else d(J.CULL_FACE);T=I}function $0(I){if(I!==x){if(l)J.lineWidth(I);x=I}}function wJ(I,JJ,s){if(I){if(YJ(J.POLYGON_OFFSET_FILL),m!==JJ||u!==s)J.polygonOffset(JJ,s),m=JJ,u=s}else d(J.POLYGON_OFFSET_FILL)}function IJ(I){if(I)YJ(J.SCISSOR_TEST);else d(J.SCISSOR_TEST)}function w(I){if(I===void 0)I=J.TEXTURE0+a-1;if(XJ!==I)J.activeTexture(I),XJ=I}function R(I,JJ,s){if(s===void 0)if(XJ===null)s=J.TEXTURE0+a-1;else s=XJ;let i=ZJ[s];if(i===void 0)i={type:void 0,texture:void 0},ZJ[s]=i;if(i.type!==I||i.texture!==JJ){if(XJ!==s)J.activeTexture(s),XJ=s;J.bindTexture(I,JJ||kJ[I]),i.type=I,i.texture=JJ}}function j(){let I=ZJ[XJ];if(I!==void 0&&I.type!==void 0)J.bindTexture(I.type,null),I.type=void 0,I.texture=void 0}function o(){try{J.compressedTexImage2D.apply(J,arguments)}catch(I){console.error("THREE.WebGLState:",I)}}function r(){try{J.compressedTexImage3D.apply(J,arguments)}catch(I){console.error("THREE.WebGLState:",I)}}function c(){try{J.texSubImage2D.apply(J,arguments)}catch(I){console.error("THREE.WebGLState:",I)}}function LJ(){try{J.texSubImage3D.apply(J,arguments)}catch(I){console.error("THREE.WebGLState:",I)}}function UJ(){try{J.compressedTexSubImage2D.apply(J,arguments)}catch(I){console.error("THREE.WebGLState:",I)}}function DJ(){try{J.compressedTexSubImage3D.apply(J,arguments)}catch(I){console.error("THREE.WebGLState:",I)}}function SJ(){try{J.texStorage2D.apply(J,arguments)}catch(I){console.error("THREE.WebGLState:",I)}}function $J(){try{J.texStorage3D.apply(J,arguments)}catch(I){console.error("THREE.WebGLState:",I)}}function FJ(){try{J.texImage2D.apply(J,arguments)}catch(I){console.error("THREE.WebGLState:",I)}}function gJ(){try{J.texImage3D.apply(J,arguments)}catch(I){console.error("THREE.WebGLState:",I)}}function PJ(I){if(n.equals(I)===!1)J.scissor(I.x,I.y,I.z,I.w),n.copy(I)}function RJ(I){if(e.equals(I)===!1)J.viewport(I.x,I.y,I.z,I.w),e.copy(I)}function yJ(I,JJ){let s=G.get(JJ);if(s===void 0)s=new WeakMap,G.set(JJ,s);let i=s.get(I);if(i===void 0)i=J.getUniformBlockIndex(JJ,I.name),s.set(I,i)}function xJ(I,JJ){let i=G.get(JJ).get(I);if(K.get(JJ)!==i)J.uniformBlockBinding(JJ,i,I.__bindingPointIndex),K.set(JJ,i)}function Q0(){J.disable(J.BLEND),J.disable(J.CULL_FACE),J.disable(J.DEPTH_TEST),J.disable(J.POLYGON_OFFSET_FILL),J.disable(J.SCISSOR_TEST),J.disable(J.STENCIL_TEST),J.disable(J.SAMPLE_ALPHA_TO_COVERAGE),J.blendEquation(J.FUNC_ADD),J.blendFunc(J.ONE,J.ZERO),J.blendFuncSeparate(J.ONE,J.ZERO,J.ONE,J.ZERO),J.blendColor(0,0,0,0),J.colorMask(!0,!0,!0,!0),J.clearColor(0,0,0,0),J.depthMask(!0),J.depthFunc(J.LESS),X.setReversed(!1),J.clearDepth(1),J.stencilMask(4294967295),J.stencilFunc(J.ALWAYS,0,4294967295),J.stencilOp(J.KEEP,J.KEEP,J.KEEP),J.clearStencil(0),J.cullFace(J.BACK),J.frontFace(J.CCW),J.polygonOffset(0,0),J.activeTexture(J.TEXTURE0),J.bindFramebuffer(J.FRAMEBUFFER,null),J.bindFramebuffer(J.DRAW_FRAMEBUFFER,null),J.bindFramebuffer(J.READ_FRAMEBUFFER,null),J.useProgram(null),J.lineWidth(1),J.scissor(0,0,J.canvas.width,J.canvas.height),J.viewport(0,0,J.canvas.width,J.canvas.height),E={},XJ=null,ZJ={},U={},q=new WeakMap,D=[],N=null,O=!1,V=null,F=null,A=null,z=null,_=null,b=null,L=null,P=new nJ(0,0,0),p=0,B=!1,k=null,T=null,x=null,m=null,u=null,n.set(0,0,J.canvas.width,J.canvas.height),e.set(0,0,J.canvas.width,J.canvas.height),Y.reset(),X.reset(),H.reset()}return{buffers:{color:Y,depth:X,stencil:H},enable:YJ,disable:d,bindFramebuffer:KJ,drawBuffers:WJ,useProgram:AJ,setBlending:lJ,setMaterial:CJ,setFlipSided:mJ,setCullFace:GJ,setLineWidth:$0,setPolygonOffset:wJ,setScissorTest:IJ,activeTexture:w,bindTexture:R,unbindTexture:j,compressedTexImage2D:o,compressedTexImage3D:r,texImage2D:FJ,texImage3D:gJ,updateUBOMapping:yJ,uniformBlockBinding:xJ,texStorage2D:SJ,texStorage3D:$J,texSubImage2D:c,texSubImage3D:LJ,compressedTexSubImage2D:UJ,compressedTexSubImage3D:DJ,scissor:PJ,viewport:RJ,reset:Q0}}function e9(J,$,Q,Z){let W=p4(Z);switch(Q){case 1021:return J*$;case 1024:return J*$;case 1025:return J*$*2;case 1028:return J*$/W.components*W.byteLength;case 1029:return J*$/W.components*W.byteLength;case 1030:return J*$*2/W.components*W.byteLength;case 1031:return J*$*2/W.components*W.byteLength;case 1022:return J*$*3/W.components*W.byteLength;case 1023:return J*$*4/W.components*W.byteLength;case 1033:return J*$*4/W.components*W.byteLength;case 33776:case 33777:return Math.floor((J+3)/4)*Math.floor(($+3)/4)*8;case 33778:case 33779:return Math.floor((J+3)/4)*Math.floor(($+3)/4)*16;case 35841:case 35843:return Math.max(J,16)*Math.max($,8)/4;case 35840:case 35842:return Math.max(J,8)*Math.max($,8)/2;case 36196:case 37492:return Math.floor((J+3)/4)*Math.floor(($+3)/4)*8;case 37496:return Math.floor((J+3)/4)*Math.floor(($+3)/4)*16;case 37808:return Math.floor((J+3)/4)*Math.floor(($+3)/4)*16;case 37809:return Math.floor((J+4)/5)*Math.floor(($+3)/4)*16;case 37810:return Math.floor((J+4)/5)*Math.floor(($+4)/5)*16;case 37811:return Math.floor((J+5)/6)*Math.floor(($+4)/5)*16;case 37812:return Math.floor((J+5)/6)*Math.floor(($+5)/6)*16;case 37813:return Math.floor((J+7)/8)*Math.floor(($+4)/5)*16;case 37814:return Math.floor((J+7)/8)*Math.floor(($+5)/6)*16;case 37815:return Math.floor((J+7)/8)*Math.floor(($+7)/8)*16;case 37816:return Math.floor((J+9)/10)*Math.floor(($+4)/5)*16;case 37817:return Math.floor((J+9)/10)*Math.floor(($+5)/6)*16;case 37818:return Math.floor((J+9)/10)*Math.floor(($+7)/8)*16;case 37819:return Math.floor((J+9)/10)*Math.floor(($+9)/10)*16;case 37820:return Math.floor((J+11)/12)*Math.floor(($+9)/10)*16;case 37821:return Math.floor((J+11)/12)*Math.floor(($+11)/12)*16;case 36492:case 36494:case 36495:return Math.ceil(J/4)*Math.ceil($/4)*16;case 36283:case 36284:return Math.ceil(J/4)*Math.ceil($/4)*8;case 36285:case 36286:return Math.ceil(J/4)*Math.ceil($/4)*16}throw Error(`Unable to determine texture byte length for ${Q} format.`)}function p4(J){switch(J){case 1009:case 1010:return{byteLength:1,components:1};case 1012:case 1011:case 1016:return{byteLength:2,components:1};case 1017:case 1018:return{byteLength:2,components:4};case 1014:case 1013:case 1015:return{byteLength:4,components:1};case 35902:return{byteLength:4,components:3}}throw Error(`Unknown texture type ${J}.`)}function g4(J,$,Q,Z,W,Y,X){let H=$.has("WEBGL_multisampled_render_to_texture")?$.get("WEBGL_multisampled_render_to_texture"):null,K=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),G=new uJ,E=new WeakMap,U,q=new WeakMap,D=!1;try{D=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch(w){}function N(w,R){return D?new OffscreenCanvas(w,R):c7("canvas")}function O(w,R,j){let o=1,r=IJ(w);if(r.width>j||r.height>j)o=j/Math.max(r.width,r.height);if(o<1)if(typeof HTMLImageElement<"u"&&w instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&w instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&w instanceof ImageBitmap||typeof VideoFrame<"u"&&w instanceof VideoFrame){let c=Math.floor(o*r.width),LJ=Math.floor(o*r.height);if(U===void 0)U=N(c,LJ);let UJ=R?N(c,LJ):U;return UJ.width=c,UJ.height=LJ,UJ.getContext("2d").drawImage(w,0,0,c,LJ),console.warn("THREE.WebGLRenderer: Texture has been resized from ("+r.width+"x"+r.height+") to ("+c+"x"+LJ+")."),UJ}else{if("data"in w)console.warn("THREE.WebGLRenderer: Image in DataTexture is too big ("+r.width+"x"+r.height+").");return w}return w}function V(w){return w.generateMipmaps}function F(w){J.generateMipmap(w)}function A(w){if(w.isWebGLCubeRenderTarget)return J.TEXTURE_CUBE_MAP;if(w.isWebGL3DRenderTarget)return J.TEXTURE_3D;if(w.isWebGLArrayRenderTarget||w.isCompressedArrayTexture)return J.TEXTURE_2D_ARRAY;return J.TEXTURE_2D}function z(w,R,j,o,r=!1){if(w!==null){if(J[w]!==void 0)return J[w];console.warn("THREE.WebGLRenderer: Attempt to use non-existing WebGL internal format '"+w+"'")}let c=R;if(R===J.RED){if(j===J.FLOAT)c=J.R32F;if(j===J.HALF_FLOAT)c=J.R16F;if(j===J.UNSIGNED_BYTE)c=J.R8}if(R===J.RED_INTEGER){if(j===J.UNSIGNED_BYTE)c=J.R8UI;if(j===J.UNSIGNED_SHORT)c=J.R16UI;if(j===J.UNSIGNED_INT)c=J.R32UI;if(j===J.BYTE)c=J.R8I;if(j===J.SHORT)c=J.R16I;if(j===J.INT)c=J.R32I}if(R===J.RG){if(j===J.FLOAT)c=J.RG32F;if(j===J.HALF_FLOAT)c=J.RG16F;if(j===J.UNSIGNED_BYTE)c=J.RG8}if(R===J.RG_INTEGER){if(j===J.UNSIGNED_BYTE)c=J.RG8UI;if(j===J.UNSIGNED_SHORT)c=J.RG16UI;if(j===J.UNSIGNED_INT)c=J.RG32UI;if(j===J.BYTE)c=J.RG8I;if(j===J.SHORT)c=J.RG16I;if(j===J.INT)c=J.RG32I}if(R===J.RGB_INTEGER){if(j===J.UNSIGNED_BYTE)c=J.RGB8UI;if(j===J.UNSIGNED_SHORT)c=J.RGB16UI;if(j===J.UNSIGNED_INT)c=J.RGB32UI;if(j===J.BYTE)c=J.RGB8I;if(j===J.SHORT)c=J.RGB16I;if(j===J.INT)c=J.RGB32I}if(R===J.RGBA_INTEGER){if(j===J.UNSIGNED_BYTE)c=J.RGBA8UI;if(j===J.UNSIGNED_SHORT)c=J.RGBA16UI;if(j===J.UNSIGNED_INT)c=J.RGBA32UI;if(j===J.BYTE)c=J.RGBA8I;if(j===J.SHORT)c=J.RGBA16I;if(j===J.INT)c=J.RGBA32I}if(R===J.RGB){if(j===J.UNSIGNED_INT_5_9_9_9_REV)c=J.RGB9_E5}if(R===J.RGBA){let LJ=r?"linear":dJ.getTransfer(o);if(j===J.FLOAT)c=J.RGBA32F;if(j===J.HALF_FLOAT)c=J.RGBA16F;if(j===J.UNSIGNED_BYTE)c=LJ==="srgb"?J.SRGB8_ALPHA8:J.RGBA8;if(j===J.UNSIGNED_SHORT_4_4_4_4)c=J.RGBA4;if(j===J.UNSIGNED_SHORT_5_5_5_1)c=J.RGB5_A1}if(c===J.R16F||c===J.R32F||c===J.RG16F||c===J.RG32F||c===J.RGBA16F||c===J.RGBA32F)$.get("EXT_color_buffer_float");return c}function _(w,R){let j;if(w){if(R===null||R===1014||R===1020)j=J.DEPTH24_STENCIL8;else if(R===1015)j=J.DEPTH32F_STENCIL8;else if(R===1012)j=J.DEPTH24_STENCIL8,console.warn("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")}else if(R===null||R===1014||R===1020)j=J.DEPTH_COMPONENT24;else if(R===1015)j=J.DEPTH_COMPONENT32F;else if(R===1012)j=J.DEPTH_COMPONENT16;return j}function b(w,R){if(V(w)===!0||w.isFramebufferTexture&&w.minFilter!==1003&&w.minFilter!==1006)return Math.log2(Math.max(R.width,R.height))+1;else if(w.mipmaps!==void 0&&w.mipmaps.length>0)return w.mipmaps.length;else if(w.isCompressedTexture&&Array.isArray(w.image))return R.mipmaps.length;else return 1}function L(w){let R=w.target;if(R.removeEventListener("dispose",L),p(R),R.isVideoTexture)E.delete(R)}function P(w){let R=w.target;R.removeEventListener("dispose",P),k(R)}function p(w){let R=Z.get(w);if(R.__webglInit===void 0)return;let j=w.source,o=q.get(j);if(o){let r=o[R.__cacheKey];if(r.usedTimes--,r.usedTimes===0)B(w);if(Object.keys(o).length===0)q.delete(j)}Z.remove(w)}function B(w){let R=Z.get(w);J.deleteTexture(R.__webglTexture);let j=w.source,o=q.get(j);delete o[R.__cacheKey],X.memory.textures--}function k(w){let R=Z.get(w);if(w.depthTexture)w.depthTexture.dispose(),Z.remove(w.depthTexture);if(w.isWebGLCubeRenderTarget)for(let o=0;o<6;o++){if(Array.isArray(R.__webglFramebuffer[o]))for(let r=0;r<R.__webglFramebuffer[o].length;r++)J.deleteFramebuffer(R.__webglFramebuffer[o][r]);else J.deleteFramebuffer(R.__webglFramebuffer[o]);if(R.__webglDepthbuffer)J.deleteRenderbuffer(R.__webglDepthbuffer[o])}else{if(Array.isArray(R.__webglFramebuffer))for(let o=0;o<R.__webglFramebuffer.length;o++)J.deleteFramebuffer(R.__webglFramebuffer[o]);else J.deleteFramebuffer(R.__webglFramebuffer);if(R.__webglDepthbuffer)J.deleteRenderbuffer(R.__webglDepthbuffer);if(R.__webglMultisampledFramebuffer)J.deleteFramebuffer(R.__webglMultisampledFramebuffer);if(R.__webglColorRenderbuffer){for(let o=0;o<R.__webglColorRenderbuffer.length;o++)if(R.__webglColorRenderbuffer[o])J.deleteRenderbuffer(R.__webglColorRenderbuffer[o])}if(R.__webglDepthRenderbuffer)J.deleteRenderbuffer(R.__webglDepthRenderbuffer)}let j=w.textures;for(let o=0,r=j.length;o<r;o++){let c=Z.get(j[o]);if(c.__webglTexture)J.deleteTexture(c.__webglTexture),X.memory.textures--;Z.remove(j[o])}Z.remove(w)}let T=0;function x(){T=0}function m(){let w=T;if(w>=W.maxTextures)console.warn("THREE.WebGLTextures: Trying to use "+w+" texture units while this GPU supports only "+W.maxTextures);return T+=1,w}function u(w){let R=[];return R.push(w.wrapS),R.push(w.wrapT),R.push(w.wrapR||0),R.push(w.magFilter),R.push(w.minFilter),R.push(w.anisotropy),R.push(w.internalFormat),R.push(w.format),R.push(w.type),R.push(w.generateMipmaps),R.push(w.premultiplyAlpha),R.push(w.flipY),R.push(w.unpackAlignment),R.push(w.colorSpace),R.join()}function a(w,R){let j=Z.get(w);if(w.isVideoTexture)$0(w);if(w.isRenderTargetTexture===!1&&w.version>0&&j.__version!==w.version){let o=w.image;if(o===null)console.warn("THREE.WebGLRenderer: Texture marked for update but no image data found.");else if(o.complete===!1)console.warn("THREE.WebGLRenderer: Texture marked for update but image is incomplete");else{e(j,w,R);return}}Q.bindTexture(J.TEXTURE_2D,j.__webglTexture,J.TEXTURE0+R)}function l(w,R){let j=Z.get(w);if(w.version>0&&j.__version!==w.version){e(j,w,R);return}Q.bindTexture(J.TEXTURE_2D_ARRAY,j.__webglTexture,J.TEXTURE0+R)}function t(w,R){let j=Z.get(w);if(w.version>0&&j.__version!==w.version){e(j,w,R);return}Q.bindTexture(J.TEXTURE_3D,j.__webglTexture,J.TEXTURE0+R)}function g(w,R){let j=Z.get(w);if(w.version>0&&j.__version!==w.version){zJ(j,w,R);return}Q.bindTexture(J.TEXTURE_CUBE_MAP,j.__webglTexture,J.TEXTURE0+R)}let XJ={[1000]:J.REPEAT,[1001]:J.CLAMP_TO_EDGE,[1002]:J.MIRRORED_REPEAT},ZJ={[1003]:J.NEAREST,[1004]:J.NEAREST_MIPMAP_NEAREST,[1005]:J.NEAREST_MIPMAP_LINEAR,[1006]:J.LINEAR,[1007]:J.LINEAR_MIPMAP_NEAREST,[1008]:J.LINEAR_MIPMAP_LINEAR},_J={[512]:J.NEVER,[519]:J.ALWAYS,[513]:J.LESS,[515]:J.LEQUAL,[514]:J.EQUAL,[518]:J.GEQUAL,[516]:J.GREATER,[517]:J.NOTEQUAL};function fJ(w,R){if(R.type===1015&&$.has("OES_texture_float_linear")===!1&&(R.magFilter===1006||R.magFilter===1007||R.magFilter===1005||R.magFilter===1008||R.minFilter===1006||R.minFilter===1007||R.minFilter===1005||R.minFilter===1008))console.warn("THREE.WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device.");if(J.texParameteri(w,J.TEXTURE_WRAP_S,XJ[R.wrapS]),J.texParameteri(w,J.TEXTURE_WRAP_T,XJ[R.wrapT]),w===J.TEXTURE_3D||w===J.TEXTURE_2D_ARRAY)J.texParameteri(w,J.TEXTURE_WRAP_R,XJ[R.wrapR]);if(J.texParameteri(w,J.TEXTURE_MAG_FILTER,ZJ[R.magFilter]),J.texParameteri(w,J.TEXTURE_MIN_FILTER,ZJ[R.minFilter]),R.compareFunction)J.texParameteri(w,J.TEXTURE_COMPARE_MODE,J.COMPARE_REF_TO_TEXTURE),J.texParameteri(w,J.TEXTURE_COMPARE_FUNC,_J[R.compareFunction]);if($.has("EXT_texture_filter_anisotropic")===!0){if(R.magFilter===1003)return;if(R.minFilter!==1005&&R.minFilter!==1008)return;if(R.type===1015&&$.has("OES_texture_float_linear")===!1)return;if(R.anisotropy>1||Z.get(R).__currentAnisotropy){let j=$.get("EXT_texture_filter_anisotropic");J.texParameterf(w,j.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(R.anisotropy,W.getMaxAnisotropy())),Z.get(R).__currentAnisotropy=R.anisotropy}}}function n(w,R){let j=!1;if(w.__webglInit===void 0)w.__webglInit=!0,R.addEventListener("dispose",L);let o=R.source,r=q.get(o);if(r===void 0)r={},q.set(o,r);let c=u(R);if(c!==w.__cacheKey){if(r[c]===void 0)r[c]={texture:J.createTexture(),usedTimes:0},X.memory.textures++,j=!0;r[c].usedTimes++;let LJ=r[w.__cacheKey];if(LJ!==void 0){if(r[w.__cacheKey].usedTimes--,LJ.usedTimes===0)B(R)}w.__cacheKey=c,w.__webglTexture=r[c].texture}return j}function e(w,R,j){let o=J.TEXTURE_2D;if(R.isDataArrayTexture||R.isCompressedArrayTexture)o=J.TEXTURE_2D_ARRAY;if(R.isData3DTexture)o=J.TEXTURE_3D;let r=n(w,R),c=R.source;Q.bindTexture(o,w.__webglTexture,J.TEXTURE0+j);let LJ=Z.get(c);if(c.version!==LJ.__version||r===!0){Q.activeTexture(J.TEXTURE0+j);let UJ=dJ.getPrimaries(dJ.workingColorSpace),DJ=R.colorSpace===""?null:dJ.getPrimaries(R.colorSpace),SJ=R.colorSpace===""||UJ===DJ?J.NONE:J.BROWSER_DEFAULT_WEBGL;J.pixelStorei(J.UNPACK_FLIP_Y_WEBGL,R.flipY),J.pixelStorei(J.UNPACK_PREMULTIPLY_ALPHA_WEBGL,R.premultiplyAlpha),J.pixelStorei(J.UNPACK_ALIGNMENT,R.unpackAlignment),J.pixelStorei(J.UNPACK_COLORSPACE_CONVERSION_WEBGL,SJ);let $J=O(R.image,!1,W.maxTextureSize);$J=wJ(R,$J);let FJ=Y.convert(R.format,R.colorSpace),gJ=Y.convert(R.type),PJ=z(R.internalFormat,FJ,gJ,R.colorSpace,R.isVideoTexture);fJ(o,R);let RJ,yJ=R.mipmaps,xJ=R.isVideoTexture!==!0,Q0=LJ.__version===void 0||r===!0,I=c.dataReady,JJ=b(R,$J);if(R.isDepthTexture){if(PJ=_(R.format===1027,R.type),Q0)if(xJ)Q.texStorage2D(J.TEXTURE_2D,1,PJ,$J.width,$J.height);else Q.texImage2D(J.TEXTURE_2D,0,PJ,$J.width,$J.height,0,FJ,gJ,null)}else if(R.isDataTexture)if(yJ.length>0){if(xJ&&Q0)Q.texStorage2D(J.TEXTURE_2D,JJ,PJ,yJ[0].width,yJ[0].height);for(let s=0,i=yJ.length;s<i;s++)if(RJ=yJ[s],xJ){if(I)Q.texSubImage2D(J.TEXTURE_2D,s,0,0,RJ.width,RJ.height,FJ,gJ,RJ.data)}else Q.texImage2D(J.TEXTURE_2D,s,PJ,RJ.width,RJ.height,0,FJ,gJ,RJ.data);R.generateMipmaps=!1}else if(xJ){if(Q0)Q.texStorage2D(J.TEXTURE_2D,JJ,PJ,$J.width,$J.height);if(I)Q.texSubImage2D(J.TEXTURE_2D,0,0,0,$J.width,$J.height,FJ,gJ,$J.data)}else Q.texImage2D(J.TEXTURE_2D,0,PJ,$J.width,$J.height,0,FJ,gJ,$J.data);else if(R.isCompressedTexture)if(R.isCompressedArrayTexture){if(xJ&&Q0)Q.texStorage3D(J.TEXTURE_2D_ARRAY,JJ,PJ,yJ[0].width,yJ[0].height,$J.depth);for(let s=0,i=yJ.length;s<i;s++)if(RJ=yJ[s],R.format!==1023)if(FJ!==null)if(xJ){if(I)if(R.layerUpdates.size>0){let VJ=e9(RJ.width,RJ.height,R.format,R.type);for(let qJ of R.layerUpdates){let hJ=RJ.data.subarray(qJ*VJ/RJ.data.BYTES_PER_ELEMENT,(qJ+1)*VJ/RJ.data.BYTES_PER_ELEMENT);Q.compressedTexSubImage3D(J.TEXTURE_2D_ARRAY,s,0,0,qJ,RJ.width,RJ.height,1,FJ,hJ)}R.clearLayerUpdates()}else Q.compressedTexSubImage3D(J.TEXTURE_2D_ARRAY,s,0,0,0,RJ.width,RJ.height,$J.depth,FJ,RJ.data)}else Q.compressedTexImage3D(J.TEXTURE_2D_ARRAY,s,PJ,RJ.width,RJ.height,$J.depth,0,RJ.data,0,0);else console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else if(xJ){if(I)Q.texSubImage3D(J.TEXTURE_2D_ARRAY,s,0,0,0,RJ.width,RJ.height,$J.depth,FJ,gJ,RJ.data)}else Q.texImage3D(J.TEXTURE_2D_ARRAY,s,PJ,RJ.width,RJ.height,$J.depth,0,FJ,gJ,RJ.data)}else{if(xJ&&Q0)Q.texStorage2D(J.TEXTURE_2D,JJ,PJ,yJ[0].width,yJ[0].height);for(let s=0,i=yJ.length;s<i;s++)if(RJ=yJ[s],R.format!==1023)if(FJ!==null)if(xJ){if(I)Q.compressedTexSubImage2D(J.TEXTURE_2D,s,0,0,RJ.width,RJ.height,FJ,RJ.data)}else Q.compressedTexImage2D(J.TEXTURE_2D,s,PJ,RJ.width,RJ.height,0,RJ.data);else console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else if(xJ){if(I)Q.texSubImage2D(J.TEXTURE_2D,s,0,0,RJ.width,RJ.height,FJ,gJ,RJ.data)}else Q.texImage2D(J.TEXTURE_2D,s,PJ,RJ.width,RJ.height,0,FJ,gJ,RJ.data)}else if(R.isDataArrayTexture)if(xJ){if(Q0)Q.texStorage3D(J.TEXTURE_2D_ARRAY,JJ,PJ,$J.width,$J.height,$J.depth);if(I)if(R.layerUpdates.size>0){let s=e9($J.width,$J.height,R.format,R.type);for(let i of R.layerUpdates){let VJ=$J.data.subarray(i*s/$J.data.BYTES_PER_ELEMENT,(i+1)*s/$J.data.BYTES_PER_ELEMENT);Q.texSubImage3D(J.TEXTURE_2D_ARRAY,0,0,0,i,$J.width,$J.height,1,FJ,gJ,VJ)}R.clearLayerUpdates()}else Q.texSubImage3D(J.TEXTURE_2D_ARRAY,0,0,0,0,$J.width,$J.height,$J.depth,FJ,gJ,$J.data)}else Q.texImage3D(J.TEXTURE_2D_ARRAY,0,PJ,$J.width,$J.height,$J.depth,0,FJ,gJ,$J.data);else if(R.isData3DTexture)if(xJ){if(Q0)Q.texStorage3D(J.TEXTURE_3D,JJ,PJ,$J.width,$J.height,$J.depth);if(I)Q.texSubImage3D(J.TEXTURE_3D,0,0,0,0,$J.width,$J.height,$J.depth,FJ,gJ,$J.data)}else Q.texImage3D(J.TEXTURE_3D,0,PJ,$J.width,$J.height,$J.depth,0,FJ,gJ,$J.data);else if(R.isFramebufferTexture){if(Q0)if(xJ)Q.texStorage2D(J.TEXTURE_2D,JJ,PJ,$J.width,$J.height);else{let{width:s,height:i}=$J;for(let VJ=0;VJ<JJ;VJ++)Q.texImage2D(J.TEXTURE_2D,VJ,PJ,s,i,0,FJ,gJ,null),s>>=1,i>>=1}}else if(yJ.length>0){if(xJ&&Q0){let s=IJ(yJ[0]);Q.texStorage2D(J.TEXTURE_2D,JJ,PJ,s.width,s.height)}for(let s=0,i=yJ.length;s<i;s++)if(RJ=yJ[s],xJ){if(I)Q.texSubImage2D(J.TEXTURE_2D,s,0,0,FJ,gJ,RJ)}else Q.texImage2D(J.TEXTURE_2D,s,PJ,FJ,gJ,RJ);R.generateMipmaps=!1}else if(xJ){if(Q0){let s=IJ($J);Q.texStorage2D(J.TEXTURE_2D,JJ,PJ,s.width,s.height)}if(I)Q.texSubImage2D(J.TEXTURE_2D,0,0,0,FJ,gJ,$J)}else Q.texImage2D(J.TEXTURE_2D,0,PJ,FJ,gJ,$J);if(V(R))F(o);if(LJ.__version=c.version,R.onUpdate)R.onUpdate(R)}w.__version=R.version}function zJ(w,R,j){if(R.image.length!==6)return;let o=n(w,R),r=R.source;Q.bindTexture(J.TEXTURE_CUBE_MAP,w.__webglTexture,J.TEXTURE0+j);let c=Z.get(r);if(r.version!==c.__version||o===!0){Q.activeTexture(J.TEXTURE0+j);let LJ=dJ.getPrimaries(dJ.workingColorSpace),UJ=R.colorSpace===""?null:dJ.getPrimaries(R.colorSpace),DJ=R.colorSpace===""||LJ===UJ?J.NONE:J.BROWSER_DEFAULT_WEBGL;J.pixelStorei(J.UNPACK_FLIP_Y_WEBGL,R.flipY),J.pixelStorei(J.UNPACK_PREMULTIPLY_ALPHA_WEBGL,R.premultiplyAlpha),J.pixelStorei(J.UNPACK_ALIGNMENT,R.unpackAlignment),J.pixelStorei(J.UNPACK_COLORSPACE_CONVERSION_WEBGL,DJ);let SJ=R.isCompressedTexture||R.image[0].isCompressedTexture,$J=R.image[0]&&R.image[0].isDataTexture,FJ=[];for(let i=0;i<6;i++){if(!SJ&&!$J)FJ[i]=O(R.image[i],!0,W.maxCubemapSize);else FJ[i]=$J?R.image[i].image:R.image[i];FJ[i]=wJ(R,FJ[i])}let gJ=FJ[0],PJ=Y.convert(R.format,R.colorSpace),RJ=Y.convert(R.type),yJ=z(R.internalFormat,PJ,RJ,R.colorSpace),xJ=R.isVideoTexture!==!0,Q0=c.__version===void 0||o===!0,I=r.dataReady,JJ=b(R,gJ);fJ(J.TEXTURE_CUBE_MAP,R);let s;if(SJ){if(xJ&&Q0)Q.texStorage2D(J.TEXTURE_CUBE_MAP,JJ,yJ,gJ.width,gJ.height);for(let i=0;i<6;i++){s=FJ[i].mipmaps;for(let VJ=0;VJ<s.length;VJ++){let qJ=s[VJ];if(R.format!==1023)if(PJ!==null)if(xJ){if(I)Q.compressedTexSubImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+i,VJ,0,0,qJ.width,qJ.height,PJ,qJ.data)}else Q.compressedTexImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+i,VJ,yJ,qJ.width,qJ.height,0,qJ.data);else console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()");else if(xJ){if(I)Q.texSubImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+i,VJ,0,0,qJ.width,qJ.height,PJ,RJ,qJ.data)}else Q.texImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+i,VJ,yJ,qJ.width,qJ.height,0,PJ,RJ,qJ.data)}}}else{if(s=R.mipmaps,xJ&&Q0){if(s.length>0)JJ++;let i=IJ(FJ[0]);Q.texStorage2D(J.TEXTURE_CUBE_MAP,JJ,yJ,i.width,i.height)}for(let i=0;i<6;i++)if($J){if(xJ){if(I)Q.texSubImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+i,0,0,0,FJ[i].width,FJ[i].height,PJ,RJ,FJ[i].data)}else Q.texImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+i,0,yJ,FJ[i].width,FJ[i].height,0,PJ,RJ,FJ[i].data);for(let VJ=0;VJ<s.length;VJ++){let hJ=s[VJ].image[i].image;if(xJ){if(I)Q.texSubImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+i,VJ+1,0,0,hJ.width,hJ.height,PJ,RJ,hJ.data)}else Q.texImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+i,VJ+1,yJ,hJ.width,hJ.height,0,PJ,RJ,hJ.data)}}else{if(xJ){if(I)Q.texSubImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+i,0,0,0,PJ,RJ,FJ[i])}else Q.texImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+i,0,yJ,PJ,RJ,FJ[i]);for(let VJ=0;VJ<s.length;VJ++){let qJ=s[VJ];if(xJ){if(I)Q.texSubImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+i,VJ+1,0,0,PJ,RJ,qJ.image[i])}else Q.texImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+i,VJ+1,yJ,PJ,RJ,qJ.image[i])}}}if(V(R))F(J.TEXTURE_CUBE_MAP);if(c.__version=r.version,R.onUpdate)R.onUpdate(R)}w.__version=R.version}function kJ(w,R,j,o,r,c){let LJ=Y.convert(j.format,j.colorSpace),UJ=Y.convert(j.type),DJ=z(j.internalFormat,LJ,UJ,j.colorSpace),SJ=Z.get(R),$J=Z.get(j);if($J.__renderTarget=R,!SJ.__hasExternalTextures){let FJ=Math.max(1,R.width>>c),gJ=Math.max(1,R.height>>c);if(r===J.TEXTURE_3D||r===J.TEXTURE_2D_ARRAY)Q.texImage3D(r,c,DJ,FJ,gJ,R.depth,0,LJ,UJ,null);else Q.texImage2D(r,c,DJ,FJ,gJ,0,LJ,UJ,null)}if(Q.bindFramebuffer(J.FRAMEBUFFER,w),GJ(R))H.framebufferTexture2DMultisampleEXT(J.FRAMEBUFFER,o,r,$J.__webglTexture,0,mJ(R));else if(r===J.TEXTURE_2D||r>=J.TEXTURE_CUBE_MAP_POSITIVE_X&&r<=J.TEXTURE_CUBE_MAP_NEGATIVE_Z)J.framebufferTexture2D(J.FRAMEBUFFER,o,r,$J.__webglTexture,c);Q.bindFramebuffer(J.FRAMEBUFFER,null)}function YJ(w,R,j){if(J.bindRenderbuffer(J.RENDERBUFFER,w),R.depthBuffer){let o=R.depthTexture,r=o&&o.isDepthTexture?o.type:null,c=_(R.stencilBuffer,r),LJ=R.stencilBuffer?J.DEPTH_STENCIL_ATTACHMENT:J.DEPTH_ATTACHMENT,UJ=mJ(R);if(GJ(R))H.renderbufferStorageMultisampleEXT(J.RENDERBUFFER,UJ,c,R.width,R.height);else if(j)J.renderbufferStorageMultisample(J.RENDERBUFFER,UJ,c,R.width,R.height);else J.renderbufferStorage(J.RENDERBUFFER,c,R.width,R.height);J.framebufferRenderbuffer(J.FRAMEBUFFER,LJ,J.RENDERBUFFER,w)}else{let o=R.textures;for(let r=0;r<o.length;r++){let c=o[r],LJ=Y.convert(c.format,c.colorSpace),UJ=Y.convert(c.type),DJ=z(c.internalFormat,LJ,UJ,c.colorSpace),SJ=mJ(R);if(j&&GJ(R)===!1)J.renderbufferStorageMultisample(J.RENDERBUFFER,SJ,DJ,R.width,R.height);else if(GJ(R))H.renderbufferStorageMultisampleEXT(J.RENDERBUFFER,SJ,DJ,R.width,R.height);else J.renderbufferStorage(J.RENDERBUFFER,DJ,R.width,R.height)}}J.bindRenderbuffer(J.RENDERBUFFER,null)}function d(w,R){if(R&&R.isWebGLCubeRenderTarget)throw Error("Depth Texture with cube render targets is not supported");if(Q.bindFramebuffer(J.FRAMEBUFFER,w),!(R.depthTexture&&R.depthTexture.isDepthTexture))throw Error("renderTarget.depthTexture must be an instance of THREE.DepthTexture");let o=Z.get(R.depthTexture);if(o.__renderTarget=R,!o.__webglTexture||R.depthTexture.image.width!==R.width||R.depthTexture.image.height!==R.height)R.depthTexture.image.width=R.width,R.depthTexture.image.height=R.height,R.depthTexture.needsUpdate=!0;a(R.depthTexture,0);let r=o.__webglTexture,c=mJ(R);if(R.depthTexture.format===1026)if(GJ(R))H.framebufferTexture2DMultisampleEXT(J.FRAMEBUFFER,J.DEPTH_ATTACHMENT,J.TEXTURE_2D,r,0,c);else J.framebufferTexture2D(J.FRAMEBUFFER,J.DEPTH_ATTACHMENT,J.TEXTURE_2D,r,0);else if(R.depthTexture.format===1027)if(GJ(R))H.framebufferTexture2DMultisampleEXT(J.FRAMEBUFFER,J.DEPTH_STENCIL_ATTACHMENT,J.TEXTURE_2D,r,0,c);else J.framebufferTexture2D(J.FRAMEBUFFER,J.DEPTH_STENCIL_ATTACHMENT,J.TEXTURE_2D,r,0);else throw Error("Unknown depthTexture format")}function KJ(w){let R=Z.get(w),j=w.isWebGLCubeRenderTarget===!0;if(R.__boundDepthTexture!==w.depthTexture){let o=w.depthTexture;if(R.__depthDisposeCallback)R.__depthDisposeCallback();if(o){let r=()=>{delete R.__boundDepthTexture,delete R.__depthDisposeCallback,o.removeEventListener("dispose",r)};o.addEventListener("dispose",r),R.__depthDisposeCallback=r}R.__boundDepthTexture=o}if(w.depthTexture&&!R.__autoAllocateDepthBuffer){if(j)throw Error("target.depthTexture not supported in Cube render targets");d(R.__webglFramebuffer,w)}else if(j){R.__webglDepthbuffer=[];for(let o=0;o<6;o++)if(Q.bindFramebuffer(J.FRAMEBUFFER,R.__webglFramebuffer[o]),R.__webglDepthbuffer[o]===void 0)R.__webglDepthbuffer[o]=J.createRenderbuffer(),YJ(R.__webglDepthbuffer[o],w,!1);else{let r=w.stencilBuffer?J.DEPTH_STENCIL_ATTACHMENT:J.DEPTH_ATTACHMENT,c=R.__webglDepthbuffer[o];J.bindRenderbuffer(J.RENDERBUFFER,c),J.framebufferRenderbuffer(J.FRAMEBUFFER,r,J.RENDERBUFFER,c)}}else if(Q.bindFramebuffer(J.FRAMEBUFFER,R.__webglFramebuffer),R.__webglDepthbuffer===void 0)R.__webglDepthbuffer=J.createRenderbuffer(),YJ(R.__webglDepthbuffer,w,!1);else{let o=w.stencilBuffer?J.DEPTH_STENCIL_ATTACHMENT:J.DEPTH_ATTACHMENT,r=R.__webglDepthbuffer;J.bindRenderbuffer(J.RENDERBUFFER,r),J.framebufferRenderbuffer(J.FRAMEBUFFER,o,J.RENDERBUFFER,r)}Q.bindFramebuffer(J.FRAMEBUFFER,null)}function WJ(w,R,j){let o=Z.get(w);if(R!==void 0)kJ(o.__webglFramebuffer,w,w.texture,J.COLOR_ATTACHMENT0,J.TEXTURE_2D,0);if(j!==void 0)KJ(w)}function AJ(w){let R=w.texture,j=Z.get(w),o=Z.get(R);w.addEventListener("dispose",P);let r=w.textures,c=w.isWebGLCubeRenderTarget===!0,LJ=r.length>1;if(!LJ){if(o.__webglTexture===void 0)o.__webglTexture=J.createTexture();o.__version=R.version,X.memory.textures++}if(c){j.__webglFramebuffer=[];for(let UJ=0;UJ<6;UJ++)if(R.mipmaps&&R.mipmaps.length>0){j.__webglFramebuffer[UJ]=[];for(let DJ=0;DJ<R.mipmaps.length;DJ++)j.__webglFramebuffer[UJ][DJ]=J.createFramebuffer()}else j.__webglFramebuffer[UJ]=J.createFramebuffer()}else{if(R.mipmaps&&R.mipmaps.length>0){j.__webglFramebuffer=[];for(let UJ=0;UJ<R.mipmaps.length;UJ++)j.__webglFramebuffer[UJ]=J.createFramebuffer()}else j.__webglFramebuffer=J.createFramebuffer();if(LJ)for(let UJ=0,DJ=r.length;UJ<DJ;UJ++){let SJ=Z.get(r[UJ]);if(SJ.__webglTexture===void 0)SJ.__webglTexture=J.createTexture(),X.memory.textures++}if(w.samples>0&&GJ(w)===!1){j.__webglMultisampledFramebuffer=J.createFramebuffer(),j.__webglColorRenderbuffer=[],Q.bindFramebuffer(J.FRAMEBUFFER,j.__webglMultisampledFramebuffer);for(let UJ=0;UJ<r.length;UJ++){let DJ=r[UJ];j.__webglColorRenderbuffer[UJ]=J.createRenderbuffer(),J.bindRenderbuffer(J.RENDERBUFFER,j.__webglColorRenderbuffer[UJ]);let SJ=Y.convert(DJ.format,DJ.colorSpace),$J=Y.convert(DJ.type),FJ=z(DJ.internalFormat,SJ,$J,DJ.colorSpace,w.isXRRenderTarget===!0),gJ=mJ(w);J.renderbufferStorageMultisample(J.RENDERBUFFER,gJ,FJ,w.width,w.height),J.framebufferRenderbuffer(J.FRAMEBUFFER,J.COLOR_ATTACHMENT0+UJ,J.RENDERBUFFER,j.__webglColorRenderbuffer[UJ])}if(J.bindRenderbuffer(J.RENDERBUFFER,null),w.depthBuffer)j.__webglDepthRenderbuffer=J.createRenderbuffer(),YJ(j.__webglDepthRenderbuffer,w,!0);Q.bindFramebuffer(J.FRAMEBUFFER,null)}}if(c){Q.bindTexture(J.TEXTURE_CUBE_MAP,o.__webglTexture),fJ(J.TEXTURE_CUBE_MAP,R);for(let UJ=0;UJ<6;UJ++)if(R.mipmaps&&R.mipmaps.length>0)for(let DJ=0;DJ<R.mipmaps.length;DJ++)kJ(j.__webglFramebuffer[UJ][DJ],w,R,J.COLOR_ATTACHMENT0,J.TEXTURE_CUBE_MAP_POSITIVE_X+UJ,DJ);else kJ(j.__webglFramebuffer[UJ],w,R,J.COLOR_ATTACHMENT0,J.TEXTURE_CUBE_MAP_POSITIVE_X+UJ,0);if(V(R))F(J.TEXTURE_CUBE_MAP);Q.unbindTexture()}else if(LJ){for(let UJ=0,DJ=r.length;UJ<DJ;UJ++){let SJ=r[UJ],$J=Z.get(SJ);if(Q.bindTexture(J.TEXTURE_2D,$J.__webglTexture),fJ(J.TEXTURE_2D,SJ),kJ(j.__webglFramebuffer,w,SJ,J.COLOR_ATTACHMENT0+UJ,J.TEXTURE_2D,0),V(SJ))F(J.TEXTURE_2D)}Q.unbindTexture()}else{let UJ=J.TEXTURE_2D;if(w.isWebGL3DRenderTarget||w.isWebGLArrayRenderTarget)UJ=w.isWebGL3DRenderTarget?J.TEXTURE_3D:J.TEXTURE_2D_ARRAY;if(Q.bindTexture(UJ,o.__webglTexture),fJ(UJ,R),R.mipmaps&&R.mipmaps.length>0)for(let DJ=0;DJ<R.mipmaps.length;DJ++)kJ(j.__webglFramebuffer[DJ],w,R,J.COLOR_ATTACHMENT0,UJ,DJ);else kJ(j.__webglFramebuffer,w,R,J.COLOR_ATTACHMENT0,UJ,0);if(V(R))F(UJ);Q.unbindTexture()}if(w.depthBuffer)KJ(w)}function pJ(w){let R=w.textures;for(let j=0,o=R.length;j<o;j++){let r=R[j];if(V(r)){let c=A(w),LJ=Z.get(r).__webglTexture;Q.bindTexture(c,LJ),F(c),Q.unbindTexture()}}}let C=[],lJ=[];function CJ(w){if(w.samples>0){if(GJ(w)===!1){let{textures:R,width:j,height:o}=w,r=J.COLOR_BUFFER_BIT,c=w.stencilBuffer?J.DEPTH_STENCIL_ATTACHMENT:J.DEPTH_ATTACHMENT,LJ=Z.get(w),UJ=R.length>1;if(UJ)for(let DJ=0;DJ<R.length;DJ++)Q.bindFramebuffer(J.FRAMEBUFFER,LJ.__webglMultisampledFramebuffer),J.framebufferRenderbuffer(J.FRAMEBUFFER,J.COLOR_ATTACHMENT0+DJ,J.RENDERBUFFER,null),Q.bindFramebuffer(J.FRAMEBUFFER,LJ.__webglFramebuffer),J.framebufferTexture2D(J.DRAW_FRAMEBUFFER,J.COLOR_ATTACHMENT0+DJ,J.TEXTURE_2D,null,0);Q.bindFramebuffer(J.READ_FRAMEBUFFER,LJ.__webglMultisampledFramebuffer),Q.bindFramebuffer(J.DRAW_FRAMEBUFFER,LJ.__webglFramebuffer);for(let DJ=0;DJ<R.length;DJ++){if(w.resolveDepthBuffer){if(w.depthBuffer)r|=J.DEPTH_BUFFER_BIT;if(w.stencilBuffer&&w.resolveStencilBuffer)r|=J.STENCIL_BUFFER_BIT}if(UJ){J.framebufferRenderbuffer(J.READ_FRAMEBUFFER,J.COLOR_ATTACHMENT0,J.RENDERBUFFER,LJ.__webglColorRenderbuffer[DJ]);let SJ=Z.get(R[DJ]).__webglTexture;J.framebufferTexture2D(J.DRAW_FRAMEBUFFER,J.COLOR_ATTACHMENT0,J.TEXTURE_2D,SJ,0)}if(J.blitFramebuffer(0,0,j,o,0,0,j,o,r,J.NEAREST),K===!0){if(C.length=0,lJ.length=0,C.push(J.COLOR_ATTACHMENT0+DJ),w.depthBuffer&&w.resolveDepthBuffer===!1)C.push(c),lJ.push(c),J.invalidateFramebuffer(J.DRAW_FRAMEBUFFER,lJ);J.invalidateFramebuffer(J.READ_FRAMEBUFFER,C)}}if(Q.bindFramebuffer(J.READ_FRAMEBUFFER,null),Q.bindFramebuffer(J.DRAW_FRAMEBUFFER,null),UJ)for(let DJ=0;DJ<R.length;DJ++){Q.bindFramebuffer(J.FRAMEBUFFER,LJ.__webglMultisampledFramebuffer),J.framebufferRenderbuffer(J.FRAMEBUFFER,J.COLOR_ATTACHMENT0+DJ,J.RENDERBUFFER,LJ.__webglColorRenderbuffer[DJ]);let SJ=Z.get(R[DJ]).__webglTexture;Q.bindFramebuffer(J.FRAMEBUFFER,LJ.__webglFramebuffer),J.framebufferTexture2D(J.DRAW_FRAMEBUFFER,J.COLOR_ATTACHMENT0+DJ,J.TEXTURE_2D,SJ,0)}Q.bindFramebuffer(J.DRAW_FRAMEBUFFER,LJ.__webglMultisampledFramebuffer)}else if(w.depthBuffer&&w.resolveDepthBuffer===!1&&K){let R=w.stencilBuffer?J.DEPTH_STENCIL_ATTACHMENT:J.DEPTH_ATTACHMENT;J.invalidateFramebuffer(J.DRAW_FRAMEBUFFER,[R])}}}function mJ(w){return Math.min(W.maxSamples,w.samples)}function GJ(w){let R=Z.get(w);return w.samples>0&&$.has("WEBGL_multisampled_render_to_texture")===!0&&R.__useRenderToTexture!==!1}function $0(w){let R=X.render.frame;if(E.get(w)!==R)E.set(w,R),w.update()}function wJ(w,R){let{colorSpace:j,format:o,type:r}=w;if(w.isCompressedTexture===!0||w.isVideoTexture===!0)return R;if(j!=="srgb-linear"&&j!=="")if(dJ.getTransfer(j)==="srgb"){if(o!==1023||r!==1009)console.warn("THREE.WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType.")}else console.error("THREE.WebGLTextures: Unsupported texture color space:",j);return R}function IJ(w){if(typeof HTMLImageElement<"u"&&w instanceof HTMLImageElement)G.width=w.naturalWidth||w.width,G.height=w.naturalHeight||w.height;else if(typeof VideoFrame<"u"&&w instanceof VideoFrame)G.width=w.displayWidth,G.height=w.displayHeight;else G.width=w.width,G.height=w.height;return G}this.allocateTextureUnit=m,this.resetTextureUnits=x,this.setTexture2D=a,this.setTexture2DArray=l,this.setTexture3D=t,this.setTextureCube=g,this.rebindTextures=WJ,this.setupRenderTarget=AJ,this.updateRenderTargetMipmap=pJ,this.updateMultisampleRenderTarget=CJ,this.setupDepthRenderbuffer=KJ,this.setupFrameBufferTexture=kJ,this.useMultisampledRTT=GJ}function m4(J,$){function Q(Z,W=""){let Y,X=dJ.getTransfer(W);if(Z===1009)return J.UNSIGNED_BYTE;if(Z===1017)return J.UNSIGNED_SHORT_4_4_4_4;if(Z===1018)return J.UNSIGNED_SHORT_5_5_5_1;if(Z===35902)return J.UNSIGNED_INT_5_9_9_9_REV;if(Z===1010)return J.BYTE;if(Z===1011)return J.SHORT;if(Z===1012)return J.UNSIGNED_SHORT;if(Z===1013)return J.INT;if(Z===1014)return J.UNSIGNED_INT;if(Z===1015)return J.FLOAT;if(Z===1016)return J.HALF_FLOAT;if(Z===1021)return J.ALPHA;if(Z===1022)return J.RGB;if(Z===1023)return J.RGBA;if(Z===1024)return J.LUMINANCE;if(Z===1025)return J.LUMINANCE_ALPHA;if(Z===1026)return J.DEPTH_COMPONENT;if(Z===1027)return J.DEPTH_STENCIL;if(Z===1028)return J.RED;if(Z===1029)return J.RED_INTEGER;if(Z===1030)return J.RG;if(Z===1031)return J.RG_INTEGER;if(Z===1033)return J.RGBA_INTEGER;if(Z===33776||Z===33777||Z===33778||Z===33779)if(X==="srgb")if(Y=$.get("WEBGL_compressed_texture_s3tc_srgb"),Y!==null){if(Z===33776)return Y.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(Z===33777)return Y.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(Z===33778)return Y.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(Z===33779)return Y.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(Y=$.get("WEBGL_compressed_texture_s3tc"),Y!==null){if(Z===33776)return Y.COMPRESSED_RGB_S3TC_DXT1_EXT;if(Z===33777)return Y.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(Z===33778)return Y.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(Z===33779)return Y.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(Z===35840||Z===35841||Z===35842||Z===35843)if(Y=$.get("WEBGL_compressed_texture_pvrtc"),Y!==null){if(Z===35840)return Y.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(Z===35841)return Y.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(Z===35842)return Y.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(Z===35843)return Y.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(Z===36196||Z===37492||Z===37496)if(Y=$.get("WEBGL_compressed_texture_etc"),Y!==null){if(Z===36196||Z===37492)return X==="srgb"?Y.COMPRESSED_SRGB8_ETC2:Y.COMPRESSED_RGB8_ETC2;if(Z===37496)return X==="srgb"?Y.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:Y.COMPRESSED_RGBA8_ETC2_EAC}else return null;if(Z===37808||Z===37809||Z===37810||Z===37811||Z===37812||Z===37813||Z===37814||Z===37815||Z===37816||Z===37817||Z===37818||Z===37819||Z===37820||Z===37821)if(Y=$.get("WEBGL_compressed_texture_astc"),Y!==null){if(Z===37808)return X==="srgb"?Y.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:Y.COMPRESSED_RGBA_ASTC_4x4_KHR;if(Z===37809)return X==="srgb"?Y.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:Y.COMPRESSED_RGBA_ASTC_5x4_KHR;if(Z===37810)return X==="srgb"?Y.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:Y.COMPRESSED_RGBA_ASTC_5x5_KHR;if(Z===37811)return X==="srgb"?Y.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:Y.COMPRESSED_RGBA_ASTC_6x5_KHR;if(Z===37812)return X==="srgb"?Y.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:Y.COMPRESSED_RGBA_ASTC_6x6_KHR;if(Z===37813)return X==="srgb"?Y.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:Y.COMPRESSED_RGBA_ASTC_8x5_KHR;if(Z===37814)return X==="srgb"?Y.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:Y.COMPRESSED_RGBA_ASTC_8x6_KHR;if(Z===37815)return X==="srgb"?Y.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:Y.COMPRESSED_RGBA_ASTC_8x8_KHR;if(Z===37816)return X==="srgb"?Y.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:Y.COMPRESSED_RGBA_ASTC_10x5_KHR;if(Z===37817)return X==="srgb"?Y.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:Y.COMPRESSED_RGBA_ASTC_10x6_KHR;if(Z===37818)return X==="srgb"?Y.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:Y.COMPRESSED_RGBA_ASTC_10x8_KHR;if(Z===37819)return X==="srgb"?Y.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:Y.COMPRESSED_RGBA_ASTC_10x10_KHR;if(Z===37820)return X==="srgb"?Y.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:Y.COMPRESSED_RGBA_ASTC_12x10_KHR;if(Z===37821)return X==="srgb"?Y.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:Y.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(Z===36492||Z===36494||Z===36495)if(Y=$.get("EXT_texture_compression_bptc"),Y!==null){if(Z===36492)return X==="srgb"?Y.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:Y.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(Z===36494)return Y.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(Z===36495)return Y.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(Z===36283||Z===36284||Z===36285||Z===36286)if(Y=$.get("EXT_texture_compression_rgtc"),Y!==null){if(Z===36492)return Y.COMPRESSED_RED_RGTC1_EXT;if(Z===36284)return Y.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(Z===36285)return Y.COMPRESSED_RED_GREEN_RGTC2_EXT;if(Z===36286)return Y.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;if(Z===1020)return J.UNSIGNED_INT_24_8;return J[Z]!==void 0?J[Z]:null}return{convert:Q}}class I$ extends k0{constructor(J=[]){super();this.isArrayCamera=!0,this.cameras=J}}class s0 extends R0{constructor(){super();this.isGroup=!0,this.type="Group"}}var u4={type:"move"};class d7{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){if(this._hand===null)this._hand=new s0,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1};return this._hand}getTargetRaySpace(){if(this._targetRay===null)this._targetRay=new s0,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new v,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new v;return this._targetRay}getGripSpace(){if(this._grip===null)this._grip=new s0,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new v,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new v;return this._grip}dispatchEvent(J){if(this._targetRay!==null)this._targetRay.dispatchEvent(J);if(this._grip!==null)this._grip.dispatchEvent(J);if(this._hand!==null)this._hand.dispatchEvent(J);return this}connect(J){if(J&&J.hand){let $=this._hand;if($)for(let Q of J.hand.values())this._getHandJoint($,Q)}return this.dispatchEvent({type:"connected",data:J}),this}disconnect(J){if(this.dispatchEvent({type:"disconnected",data:J}),this._targetRay!==null)this._targetRay.visible=!1;if(this._grip!==null)this._grip.visible=!1;if(this._hand!==null)this._hand.visible=!1;return this}update(J,$,Q){let Z=null,W=null,Y=null,X=this._targetRay,H=this._grip,K=this._hand;if(J&&$.session.visibilityState!=="visible-blurred"){if(K&&J.hand){Y=!0;for(let N of J.hand.values()){let O=$.getJointPose(N,Q),V=this._getHandJoint(K,N);if(O!==null)V.matrix.fromArray(O.transform.matrix),V.matrix.decompose(V.position,V.rotation,V.scale),V.matrixWorldNeedsUpdate=!0,V.jointRadius=O.radius;V.visible=O!==null}let G=K.joints["index-finger-tip"],E=K.joints["thumb-tip"],U=G.position.distanceTo(E.position),q=0.02,D=0.005;if(K.inputState.pinching&&U>q+D)K.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:J.handedness,target:this});else if(!K.inputState.pinching&&U<=q-D)K.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:J.handedness,target:this})}else if(H!==null&&J.gripSpace){if(W=$.getPose(J.gripSpace,Q),W!==null){if(H.matrix.fromArray(W.transform.matrix),H.matrix.decompose(H.position,H.rotation,H.scale),H.matrixWorldNeedsUpdate=!0,W.linearVelocity)H.hasLinearVelocity=!0,H.linearVelocity.copy(W.linearVelocity);else H.hasLinearVelocity=!1;if(W.angularVelocity)H.hasAngularVelocity=!0,H.angularVelocity.copy(W.angularVelocity);else H.hasAngularVelocity=!1}}if(X!==null){if(Z=$.getPose(J.targetRaySpace,Q),Z===null&&W!==null)Z=W;if(Z!==null){if(X.matrix.fromArray(Z.transform.matrix),X.matrix.decompose(X.position,X.rotation,X.scale),X.matrixWorldNeedsUpdate=!0,Z.linearVelocity)X.hasLinearVelocity=!0,X.linearVelocity.copy(Z.linearVelocity);else X.hasLinearVelocity=!1;if(Z.angularVelocity)X.hasAngularVelocity=!0,X.angularVelocity.copy(Z.angularVelocity);else X.hasAngularVelocity=!1;this.dispatchEvent(u4)}}}if(X!==null)X.visible=Z!==null;if(H!==null)H.visible=W!==null;if(K!==null)K.visible=Y!==null;return this}_getHandJoint(J,$){if(J.joints[$.jointName]===void 0){let Q=new s0;Q.matrixAutoUpdate=!1,Q.visible=!1,J.joints[$.jointName]=Q,J.add(Q)}return J.joints[$.jointName]}}var l4=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,d4=`
uniform sampler2DArray depthColor;
uniform float depthWidth;
uniform float depthHeight;

void main() {

	vec2 coord = vec2( gl_FragCoord.x / depthWidth, gl_FragCoord.y / depthHeight );

	if ( coord.x >= 1.0 ) {

		gl_FragDepth = texture( depthColor, vec3( coord.x - 1.0, coord.y, 1 ) ).r;

	} else {

		gl_FragDepth = texture( depthColor, vec3( coord.x, coord.y, 0 ) ).r;

	}

}`;class S${constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(J,$,Q){if(this.texture===null){let Z=new M0,W=J.properties.get(Z);if(W.__webglTexture=$.texture,$.depthNear!=Q.depthNear||$.depthFar!=Q.depthFar)this.depthNear=$.depthNear,this.depthFar=$.depthFar;this.texture=Z}}getMesh(J){if(this.texture!==null){if(this.mesh===null){let $=J.cameras[0].viewport,Q=new a0({vertexShader:l4,fragmentShader:d4,uniforms:{depthColor:{value:this.texture},depthWidth:{value:$.z},depthHeight:{value:$.w}}});this.mesh=new T0(new a7(20,20),Q)}}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}}class y$ extends O6{constructor(J,$){super();let Q=this,Z=null,W=1,Y=null,X="local-floor",H=1,K=null,G=null,E=null,U=null,q=null,D=null,N=new S$,O=$.getContextAttributes(),V=null,F=null,A=[],z=[],_=new uJ,b=null,L=new k0;L.viewport=new H0;let P=new k0;P.viewport=new H0;let p=[L,P],B=new I$,k=null,T=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(n){let e=A[n];if(e===void 0)e=new d7,A[n]=e;return e.getTargetRaySpace()},this.getControllerGrip=function(n){let e=A[n];if(e===void 0)e=new d7,A[n]=e;return e.getGripSpace()},this.getHand=function(n){let e=A[n];if(e===void 0)e=new d7,A[n]=e;return e.getHandSpace()};function x(n){let e=z.indexOf(n.inputSource);if(e===-1)return;let zJ=A[e];if(zJ!==void 0)zJ.update(n.inputSource,n.frame,K||Y),zJ.dispatchEvent({type:n.type,data:n.inputSource})}function m(){Z.removeEventListener("select",x),Z.removeEventListener("selectstart",x),Z.removeEventListener("selectend",x),Z.removeEventListener("squeeze",x),Z.removeEventListener("squeezestart",x),Z.removeEventListener("squeezeend",x),Z.removeEventListener("end",m),Z.removeEventListener("inputsourceschange",u);for(let n=0;n<A.length;n++){let e=z[n];if(e===null)continue;z[n]=null,A[n].disconnect(e)}k=null,T=null,N.reset(),J.setRenderTarget(V),q=null,U=null,E=null,Z=null,F=null,fJ.stop(),Q.isPresenting=!1,J.setPixelRatio(b),J.setSize(_.width,_.height,!1),Q.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(n){if(W=n,Q.isPresenting===!0)console.warn("THREE.WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(n){if(X=n,Q.isPresenting===!0)console.warn("THREE.WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return K||Y},this.setReferenceSpace=function(n){K=n},this.getBaseLayer=function(){return U!==null?U:q},this.getBinding=function(){return E},this.getFrame=function(){return D},this.getSession=function(){return Z},this.setSession=async function(n){if(Z=n,Z!==null){if(V=J.getRenderTarget(),Z.addEventListener("select",x),Z.addEventListener("selectstart",x),Z.addEventListener("selectend",x),Z.addEventListener("squeeze",x),Z.addEventListener("squeezestart",x),Z.addEventListener("squeezeend",x),Z.addEventListener("end",m),Z.addEventListener("inputsourceschange",u),O.xrCompatible!==!0)await $.makeXRCompatible();if(b=J.getPixelRatio(),J.getSize(_),Z.renderState.layers===void 0){let e={antialias:O.antialias,alpha:!0,depth:O.depth,stencil:O.stencil,framebufferScaleFactor:W};q=new XRWebGLLayer(Z,$,e),Z.updateRenderState({baseLayer:q}),J.setPixelRatio(1),J.setSize(q.framebufferWidth,q.framebufferHeight,!1),F=new X6(q.framebufferWidth,q.framebufferHeight,{format:1023,type:1009,colorSpace:J.outputColorSpace,stencilBuffer:O.stencil})}else{let e=null,zJ=null,kJ=null;if(O.depth)kJ=O.stencil?$.DEPTH24_STENCIL8:$.DEPTH_COMPONENT24,e=O.stencil?1027:1026,zJ=O.stencil?1020:1014;let YJ={colorFormat:$.RGBA8,depthFormat:kJ,scaleFactor:W};E=new XRWebGLBinding(Z,$),U=E.createProjectionLayer(YJ),Z.updateRenderState({layers:[U]}),J.setPixelRatio(1),J.setSize(U.textureWidth,U.textureHeight,!1),F=new X6(U.textureWidth,U.textureHeight,{format:1023,type:1009,depthTexture:new n8(U.textureWidth,U.textureHeight,zJ,void 0,void 0,void 0,void 0,void 0,void 0,e),stencilBuffer:O.stencil,colorSpace:J.outputColorSpace,samples:O.antialias?4:0,resolveDepthBuffer:U.ignoreDepthValues===!1})}F.isXRRenderTarget=!0,this.setFoveation(H),K=null,Y=await Z.requestReferenceSpace(X),fJ.setContext(Z),fJ.start(),Q.isPresenting=!0,Q.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(Z!==null)return Z.environmentBlendMode},this.getDepthTexture=function(){return N.getDepthTexture()};function u(n){for(let e=0;e<n.removed.length;e++){let zJ=n.removed[e],kJ=z.indexOf(zJ);if(kJ>=0)z[kJ]=null,A[kJ].disconnect(zJ)}for(let e=0;e<n.added.length;e++){let zJ=n.added[e],kJ=z.indexOf(zJ);if(kJ===-1){for(let d=0;d<A.length;d++)if(d>=z.length){z.push(zJ),kJ=d;break}else if(z[d]===null){z[d]=zJ,kJ=d;break}if(kJ===-1)break}let YJ=A[kJ];if(YJ)YJ.connect(zJ)}}let a=new v,l=new v;function t(n,e,zJ){a.setFromMatrixPosition(e.matrixWorld),l.setFromMatrixPosition(zJ.matrixWorld);let kJ=a.distanceTo(l),YJ=e.projectionMatrix.elements,d=zJ.projectionMatrix.elements,KJ=YJ[14]/(YJ[10]-1),WJ=YJ[14]/(YJ[10]+1),AJ=(YJ[9]+1)/YJ[5],pJ=(YJ[9]-1)/YJ[5],C=(YJ[8]-1)/YJ[0],lJ=(d[8]+1)/d[0],CJ=KJ*C,mJ=KJ*lJ,GJ=kJ/(-C+lJ),$0=GJ*-C;if(e.matrixWorld.decompose(n.position,n.quaternion,n.scale),n.translateX($0),n.translateZ(GJ),n.matrixWorld.compose(n.position,n.quaternion,n.scale),n.matrixWorldInverse.copy(n.matrixWorld).invert(),YJ[10]===-1)n.projectionMatrix.copy(e.projectionMatrix),n.projectionMatrixInverse.copy(e.projectionMatrixInverse);else{let wJ=KJ+GJ,IJ=WJ+GJ,w=CJ-$0,R=mJ+(kJ-$0),j=AJ*WJ/IJ*wJ,o=pJ*WJ/IJ*wJ;n.projectionMatrix.makePerspective(w,R,j,o,wJ,IJ),n.projectionMatrixInverse.copy(n.projectionMatrix).invert()}}function g(n,e){if(e===null)n.matrixWorld.copy(n.matrix);else n.matrixWorld.multiplyMatrices(e.matrixWorld,n.matrix);n.matrixWorldInverse.copy(n.matrixWorld).invert()}this.updateCamera=function(n){if(Z===null)return;let{near:e,far:zJ}=n;if(N.texture!==null){if(N.depthNear>0)e=N.depthNear;if(N.depthFar>0)zJ=N.depthFar}if(B.near=P.near=L.near=e,B.far=P.far=L.far=zJ,k!==B.near||T!==B.far)Z.updateRenderState({depthNear:B.near,depthFar:B.far}),k=B.near,T=B.far;L.layers.mask=n.layers.mask|2,P.layers.mask=n.layers.mask|4,B.layers.mask=L.layers.mask|P.layers.mask;let kJ=n.parent,YJ=B.cameras;g(B,kJ);for(let d=0;d<YJ.length;d++)g(YJ[d],kJ);if(YJ.length===2)t(B,L,P);else B.projectionMatrix.copy(L.projectionMatrix);XJ(n,B,kJ)};function XJ(n,e,zJ){if(zJ===null)n.matrix.copy(e.matrixWorld);else n.matrix.copy(zJ.matrixWorld),n.matrix.invert(),n.matrix.multiply(e.matrixWorld);if(n.matrix.decompose(n.position,n.quaternion,n.scale),n.updateMatrixWorld(!0),n.projectionMatrix.copy(e.projectionMatrix),n.projectionMatrixInverse.copy(e.projectionMatrixInverse),n.isPerspectiveCamera)n.fov=v8*2*Math.atan(1/n.projectionMatrix.elements[5]),n.zoom=1}this.getCamera=function(){return B},this.getFoveation=function(){if(U===null&&q===null)return;return H},this.setFoveation=function(n){if(H=n,U!==null)U.fixedFoveation=n;if(q!==null&&q.fixedFoveation!==void 0)q.fixedFoveation=n},this.hasDepthSensing=function(){return N.texture!==null},this.getDepthSensingMesh=function(){return N.getMesh(B)};let ZJ=null;function _J(n,e){if(G=e.getViewerPose(K||Y),D=e,G!==null){let zJ=G.views;if(q!==null)J.setRenderTargetFramebuffer(F,q.framebuffer),J.setRenderTarget(F);let kJ=!1;if(zJ.length!==B.cameras.length)B.cameras.length=0,kJ=!0;for(let d=0;d<zJ.length;d++){let KJ=zJ[d],WJ=null;if(q!==null)WJ=q.getViewport(KJ);else{let pJ=E.getViewSubImage(U,KJ);if(WJ=pJ.viewport,d===0)J.setRenderTargetTextures(F,pJ.colorTexture,U.ignoreDepthValues?void 0:pJ.depthStencilTexture),J.setRenderTarget(F)}let AJ=p[d];if(AJ===void 0)AJ=new k0,AJ.layers.enable(d),AJ.viewport=new H0,p[d]=AJ;if(AJ.matrix.fromArray(KJ.transform.matrix),AJ.matrix.decompose(AJ.position,AJ.quaternion,AJ.scale),AJ.projectionMatrix.fromArray(KJ.projectionMatrix),AJ.projectionMatrixInverse.copy(AJ.projectionMatrix).invert(),AJ.viewport.set(WJ.x,WJ.y,WJ.width,WJ.height),d===0)B.matrix.copy(AJ.matrix),B.matrix.decompose(B.position,B.quaternion,B.scale);if(kJ===!0)B.cameras.push(AJ)}let YJ=Z.enabledFeatures;if(YJ&&YJ.includes("depth-sensing")){let d=E.getDepthInformation(zJ[0]);if(d&&d.isValid&&d.texture)N.init(J,d,Z.renderState)}}for(let zJ=0;zJ<A.length;zJ++){let kJ=z[zJ],YJ=A[zJ];if(kJ!==null&&YJ!==void 0)YJ.update(kJ,e,K||Y)}if(ZJ)ZJ(n,e);if(e.detectedPlanes)Q.dispatchEvent({type:"planesdetected",data:e});D=null}let fJ=new N$;fJ.setAnimationLoop(_J),this.setAnimationLoop=function(n){ZJ=n},this.dispose=function(){}}}var D6=new o0,c4=new Z0;function n4(J,$){function Q(V,F){if(V.matrixAutoUpdate===!0)V.updateMatrix();F.value.copy(V.matrix)}function Z(V,F){if(F.color.getRGB(V.fogColor.value,F$(J)),F.isFog)V.fogNear.value=F.near,V.fogFar.value=F.far;else if(F.isFogExp2)V.fogDensity.value=F.density}function W(V,F,A,z,_){if(F.isMeshBasicMaterial)Y(V,F);else if(F.isMeshLambertMaterial)Y(V,F);else if(F.isMeshToonMaterial)Y(V,F),U(V,F);else if(F.isMeshPhongMaterial)Y(V,F),E(V,F);else if(F.isMeshStandardMaterial){if(Y(V,F),q(V,F),F.isMeshPhysicalMaterial)D(V,F,_)}else if(F.isMeshMatcapMaterial)Y(V,F),N(V,F);else if(F.isMeshDepthMaterial)Y(V,F);else if(F.isMeshDistanceMaterial)Y(V,F),O(V,F);else if(F.isMeshNormalMaterial)Y(V,F);else if(F.isLineBasicMaterial){if(X(V,F),F.isLineDashedMaterial)H(V,F)}else if(F.isPointsMaterial)K(V,F,A,z);else if(F.isSpriteMaterial)G(V,F);else if(F.isShadowMaterial)V.color.value.copy(F.color),V.opacity.value=F.opacity;else if(F.isShaderMaterial)F.uniformsNeedUpdate=!1}function Y(V,F){if(V.opacity.value=F.opacity,F.color)V.diffuse.value.copy(F.color);if(F.emissive)V.emissive.value.copy(F.emissive).multiplyScalar(F.emissiveIntensity);if(F.map)V.map.value=F.map,Q(F.map,V.mapTransform);if(F.alphaMap)V.alphaMap.value=F.alphaMap,Q(F.alphaMap,V.alphaMapTransform);if(F.bumpMap){if(V.bumpMap.value=F.bumpMap,Q(F.bumpMap,V.bumpMapTransform),V.bumpScale.value=F.bumpScale,F.side===1)V.bumpScale.value*=-1}if(F.normalMap){if(V.normalMap.value=F.normalMap,Q(F.normalMap,V.normalMapTransform),V.normalScale.value.copy(F.normalScale),F.side===1)V.normalScale.value.negate()}if(F.displacementMap)V.displacementMap.value=F.displacementMap,Q(F.displacementMap,V.displacementMapTransform),V.displacementScale.value=F.displacementScale,V.displacementBias.value=F.displacementBias;if(F.emissiveMap)V.emissiveMap.value=F.emissiveMap,Q(F.emissiveMap,V.emissiveMapTransform);if(F.specularMap)V.specularMap.value=F.specularMap,Q(F.specularMap,V.specularMapTransform);if(F.alphaTest>0)V.alphaTest.value=F.alphaTest;let A=$.get(F),z=A.envMap,_=A.envMapRotation;if(z){if(V.envMap.value=z,D6.copy(_),D6.x*=-1,D6.y*=-1,D6.z*=-1,z.isCubeTexture&&z.isRenderTargetTexture===!1)D6.y*=-1,D6.z*=-1;V.envMapRotation.value.setFromMatrix4(c4.makeRotationFromEuler(D6)),V.flipEnvMap.value=z.isCubeTexture&&z.isRenderTargetTexture===!1?-1:1,V.reflectivity.value=F.reflectivity,V.ior.value=F.ior,V.refractionRatio.value=F.refractionRatio}if(F.lightMap)V.lightMap.value=F.lightMap,V.lightMapIntensity.value=F.lightMapIntensity,Q(F.lightMap,V.lightMapTransform);if(F.aoMap)V.aoMap.value=F.aoMap,V.aoMapIntensity.value=F.aoMapIntensity,Q(F.aoMap,V.aoMapTransform)}function X(V,F){if(V.diffuse.value.copy(F.color),V.opacity.value=F.opacity,F.map)V.map.value=F.map,Q(F.map,V.mapTransform)}function H(V,F){V.dashSize.value=F.dashSize,V.totalSize.value=F.dashSize+F.gapSize,V.scale.value=F.scale}function K(V,F,A,z){if(V.diffuse.value.copy(F.color),V.opacity.value=F.opacity,V.size.value=F.size*A,V.scale.value=z*0.5,F.map)V.map.value=F.map,Q(F.map,V.uvTransform);if(F.alphaMap)V.alphaMap.value=F.alphaMap,Q(F.alphaMap,V.alphaMapTransform);if(F.alphaTest>0)V.alphaTest.value=F.alphaTest}function G(V,F){if(V.diffuse.value.copy(F.color),V.opacity.value=F.opacity,V.rotation.value=F.rotation,F.map)V.map.value=F.map,Q(F.map,V.mapTransform);if(F.alphaMap)V.alphaMap.value=F.alphaMap,Q(F.alphaMap,V.alphaMapTransform);if(F.alphaTest>0)V.alphaTest.value=F.alphaTest}function E(V,F){V.specular.value.copy(F.specular),V.shininess.value=Math.max(F.shininess,0.0001)}function U(V,F){if(F.gradientMap)V.gradientMap.value=F.gradientMap}function q(V,F){if(V.metalness.value=F.metalness,F.metalnessMap)V.metalnessMap.value=F.metalnessMap,Q(F.metalnessMap,V.metalnessMapTransform);if(V.roughness.value=F.roughness,F.roughnessMap)V.roughnessMap.value=F.roughnessMap,Q(F.roughnessMap,V.roughnessMapTransform);if(F.envMap)V.envMapIntensity.value=F.envMapIntensity}function D(V,F,A){if(V.ior.value=F.ior,F.sheen>0){if(V.sheenColor.value.copy(F.sheenColor).multiplyScalar(F.sheen),V.sheenRoughness.value=F.sheenRoughness,F.sheenColorMap)V.sheenColorMap.value=F.sheenColorMap,Q(F.sheenColorMap,V.sheenColorMapTransform);if(F.sheenRoughnessMap)V.sheenRoughnessMap.value=F.sheenRoughnessMap,Q(F.sheenRoughnessMap,V.sheenRoughnessMapTransform)}if(F.clearcoat>0){if(V.clearcoat.value=F.clearcoat,V.clearcoatRoughness.value=F.clearcoatRoughness,F.clearcoatMap)V.clearcoatMap.value=F.clearcoatMap,Q(F.clearcoatMap,V.clearcoatMapTransform);if(F.clearcoatRoughnessMap)V.clearcoatRoughnessMap.value=F.clearcoatRoughnessMap,Q(F.clearcoatRoughnessMap,V.clearcoatRoughnessMapTransform);if(F.clearcoatNormalMap){if(V.clearcoatNormalMap.value=F.clearcoatNormalMap,Q(F.clearcoatNormalMap,V.clearcoatNormalMapTransform),V.clearcoatNormalScale.value.copy(F.clearcoatNormalScale),F.side===1)V.clearcoatNormalScale.value.negate()}}if(F.dispersion>0)V.dispersion.value=F.dispersion;if(F.iridescence>0){if(V.iridescence.value=F.iridescence,V.iridescenceIOR.value=F.iridescenceIOR,V.iridescenceThicknessMinimum.value=F.iridescenceThicknessRange[0],V.iridescenceThicknessMaximum.value=F.iridescenceThicknessRange[1],F.iridescenceMap)V.iridescenceMap.value=F.iridescenceMap,Q(F.iridescenceMap,V.iridescenceMapTransform);if(F.iridescenceThicknessMap)V.iridescenceThicknessMap.value=F.iridescenceThicknessMap,Q(F.iridescenceThicknessMap,V.iridescenceThicknessMapTransform)}if(F.transmission>0){if(V.transmission.value=F.transmission,V.transmissionSamplerMap.value=A.texture,V.transmissionSamplerSize.value.set(A.width,A.height),F.transmissionMap)V.transmissionMap.value=F.transmissionMap,Q(F.transmissionMap,V.transmissionMapTransform);if(V.thickness.value=F.thickness,F.thicknessMap)V.thicknessMap.value=F.thicknessMap,Q(F.thicknessMap,V.thicknessMapTransform);V.attenuationDistance.value=F.attenuationDistance,V.attenuationColor.value.copy(F.attenuationColor)}if(F.anisotropy>0){if(V.anisotropyVector.value.set(F.anisotropy*Math.cos(F.anisotropyRotation),F.anisotropy*Math.sin(F.anisotropyRotation)),F.anisotropyMap)V.anisotropyMap.value=F.anisotropyMap,Q(F.anisotropyMap,V.anisotropyMapTransform)}if(V.specularIntensity.value=F.specularIntensity,V.specularColor.value.copy(F.specularColor),F.specularColorMap)V.specularColorMap.value=F.specularColorMap,Q(F.specularColorMap,V.specularColorMapTransform);if(F.specularIntensityMap)V.specularIntensityMap.value=F.specularIntensityMap,Q(F.specularIntensityMap,V.specularIntensityMapTransform)}function N(V,F){if(F.matcap)V.matcap.value=F.matcap}function O(V,F){let A=$.get(F).light;V.referencePosition.value.setFromMatrixPosition(A.matrixWorld),V.nearDistance.value=A.shadow.camera.near,V.farDistance.value=A.shadow.camera.far}return{refreshFogUniforms:Z,refreshMaterialUniforms:W}}function s4(J,$,Q,Z){let W={},Y={},X=[],H=J.getParameter(J.MAX_UNIFORM_BUFFER_BINDINGS);function K(A,z){let _=z.program;Z.uniformBlockBinding(A,_)}function G(A,z){let _=W[A.id];if(_===void 0)N(A),_=E(A),W[A.id]=_,A.addEventListener("dispose",V);let b=z.program;Z.updateUBOMapping(A,b);let L=$.render.frame;if(Y[A.id]!==L)q(A),Y[A.id]=L}function E(A){let z=U();A.__bindingPointIndex=z;let _=J.createBuffer(),b=A.__size,L=A.usage;return J.bindBuffer(J.UNIFORM_BUFFER,_),J.bufferData(J.UNIFORM_BUFFER,b,L),J.bindBuffer(J.UNIFORM_BUFFER,null),J.bindBufferBase(J.UNIFORM_BUFFER,z,_),_}function U(){for(let A=0;A<H;A++)if(X.indexOf(A)===-1)return X.push(A),A;return console.error("THREE.WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function q(A){let z=W[A.id],_=A.uniforms,b=A.__cache;J.bindBuffer(J.UNIFORM_BUFFER,z);for(let L=0,P=_.length;L<P;L++){let p=Array.isArray(_[L])?_[L]:[_[L]];for(let B=0,k=p.length;B<k;B++){let T=p[B];if(D(T,L,B,b)===!0){let x=T.__offset,m=Array.isArray(T.value)?T.value:[T.value],u=0;for(let a=0;a<m.length;a++){let l=m[a],t=O(l);if(typeof l==="number"||typeof l==="boolean")T.__data[0]=l,J.bufferSubData(J.UNIFORM_BUFFER,x+u,T.__data);else if(l.isMatrix3)T.__data[0]=l.elements[0],T.__data[1]=l.elements[1],T.__data[2]=l.elements[2],T.__data[3]=0,T.__data[4]=l.elements[3],T.__data[5]=l.elements[4],T.__data[6]=l.elements[5],T.__data[7]=0,T.__data[8]=l.elements[6],T.__data[9]=l.elements[7],T.__data[10]=l.elements[8],T.__data[11]=0;else l.toArray(T.__data,u),u+=t.storage/Float32Array.BYTES_PER_ELEMENT}J.bufferSubData(J.UNIFORM_BUFFER,x,T.__data)}}}J.bindBuffer(J.UNIFORM_BUFFER,null)}function D(A,z,_,b){let L=A.value,P=z+"_"+_;if(b[P]===void 0){if(typeof L==="number"||typeof L==="boolean")b[P]=L;else b[P]=L.clone();return!0}else{let p=b[P];if(typeof L==="number"||typeof L==="boolean"){if(p!==L)return b[P]=L,!0}else if(p.equals(L)===!1)return p.copy(L),!0}return!1}function N(A){let z=A.uniforms,_=0,b=16;for(let P=0,p=z.length;P<p;P++){let B=Array.isArray(z[P])?z[P]:[z[P]];for(let k=0,T=B.length;k<T;k++){let x=B[k],m=Array.isArray(x.value)?x.value:[x.value];for(let u=0,a=m.length;u<a;u++){let l=m[u],t=O(l),g=_%b,XJ=g%t.boundary,ZJ=g+XJ;if(_+=XJ,ZJ!==0&&b-ZJ<t.storage)_+=b-ZJ;x.__data=new Float32Array(t.storage/Float32Array.BYTES_PER_ELEMENT),x.__offset=_,_+=t.storage}}}let L=_%b;if(L>0)_+=b-L;return A.__size=_,A.__cache={},this}function O(A){let z={boundary:0,storage:0};if(typeof A==="number"||typeof A==="boolean")z.boundary=4,z.storage=4;else if(A.isVector2)z.boundary=8,z.storage=8;else if(A.isVector3||A.isColor)z.boundary=16,z.storage=12;else if(A.isVector4)z.boundary=16,z.storage=16;else if(A.isMatrix3)z.boundary=48,z.storage=48;else if(A.isMatrix4)z.boundary=64,z.storage=64;else if(A.isTexture)console.warn("THREE.WebGLRenderer: Texture samplers can not be part of an uniforms group.");else console.warn("THREE.WebGLRenderer: Unsupported uniform value type.",A);return z}function V(A){let z=A.target;z.removeEventListener("dispose",V);let _=X.indexOf(z.__bindingPointIndex);X.splice(_,1),J.deleteBuffer(W[z.id]),delete W[z.id],delete Y[z.id]}function F(){for(let A in W)J.deleteBuffer(W[A]);X=[],W={},Y={}}return{bind:K,update:G,dispose:F}}class s8{constructor(J={}){let{canvas:$=r$(),context:Q=null,depth:Z=!0,stencil:W=!1,alpha:Y=!1,antialias:X=!1,premultipliedAlpha:H=!0,preserveDrawingBuffer:K=!1,powerPreference:G="default",failIfMajorPerformanceCaveat:E=!1,reverseDepthBuffer:U=!1}=J;this.isWebGLRenderer=!0;let q;if(Q!==null){if(typeof WebGLRenderingContext<"u"&&Q instanceof WebGLRenderingContext)throw Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");q=Q.getContextAttributes().alpha}else q=Y;let D=new Uint32Array(4),N=new Int32Array(4),O=null,V=null,F=[],A=[];this.domElement=$,this.debug={checkShaderErrors:!0,onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this._outputColorSpace="srgb",this.toneMapping=0,this.toneMappingExposure=1;let z=this,_=!1,b=0,L=0,P=null,p=-1,B=null,k=new H0,T=new H0,x=null,m=new nJ(0),u=0,a=$.width,l=$.height,t=1,g=null,XJ=null,ZJ=new H0(0,0,a,l),_J=new H0(0,0,a,l),fJ=!1,n=new d8,e=!1,zJ=!1,kJ=new Z0,YJ=new Z0,d=new v,KJ=new H0,WJ={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0},AJ=!1;function pJ(){return P===null?t:1}let C=Q;function lJ(M,y){return $.getContext(M,y)}try{let M={alpha:!0,depth:Z,stencil:W,antialias:X,premultipliedAlpha:H,preserveDrawingBuffer:K,powerPreference:G,failIfMajorPerformanceCaveat:E};if("setAttribute"in $)$.setAttribute("data-engine","three.js r170");if($.addEventListener("webglcontextlost",s,!1),$.addEventListener("webglcontextrestored",i,!1),$.addEventListener("webglcontextcreationerror",VJ,!1),C===null){if(C=lJ("webgl2",M),C===null)if(lJ("webgl2"))throw Error("Error creating WebGL context with your selected attributes.");else throw Error("Error creating WebGL context.")}}catch(M){throw console.error("THREE.WebGLRenderer: "+M.message),M}let CJ,mJ,GJ,$0,wJ,IJ,w,R,j,o,r,c,LJ,UJ,DJ,SJ,$J,FJ,gJ,PJ,RJ,yJ,xJ,Q0;function I(){if(CJ=new GW(C),CJ.init(),yJ=new m4(C,CJ),mJ=new ZW(C,CJ,J,yJ),GJ=new x4(C,CJ),mJ.reverseDepthBuffer&&U)GJ.buffers.depth.setReversed(!0);$0=new EW(C),wJ=new L4,IJ=new g4(C,CJ,GJ,wJ,mJ,yJ,$0),w=new YW(z),R=new KW(z),j=new M5(C),xJ=new $W(C,j),o=new UW(C,j,$0,xJ),r=new FW(C,o,j,$0),gJ=new VW(C,mJ,IJ),SJ=new WW(wJ),c=new w4(z,w,R,CJ,mJ,xJ,SJ),LJ=new n4(z,wJ),UJ=new C4,DJ=new v4(CJ),FJ=new JW(z,w,R,GJ,r,q,H),$J=new h4(z,r,mJ),Q0=new s4(C,$0,mJ,GJ),PJ=new QW(C,CJ,$0),RJ=new qW(C,CJ,$0),$0.programs=c.programs,z.capabilities=mJ,z.extensions=CJ,z.properties=wJ,z.renderLists=UJ,z.shadowMap=$J,z.state=GJ,z.info=$0}I();let JJ=new y$(z,C);this.xr=JJ,this.getContext=function(){return C},this.getContextAttributes=function(){return C.getContextAttributes()},this.forceContextLoss=function(){let M=CJ.get("WEBGL_lose_context");if(M)M.loseContext()},this.forceContextRestore=function(){let M=CJ.get("WEBGL_lose_context");if(M)M.restoreContext()},this.getPixelRatio=function(){return t},this.setPixelRatio=function(M){if(M===void 0)return;t=M,this.setSize(a,l,!1)},this.getSize=function(M){return M.set(a,l)},this.setSize=function(M,y,f=!0){if(JJ.isPresenting){console.warn("THREE.WebGLRenderer: Can't change size while VR device is presenting.");return}if(a=M,l=y,$.width=Math.floor(M*t),$.height=Math.floor(y*t),f===!0)$.style.width=M+"px",$.style.height=y+"px";this.setViewport(0,0,M,y)},this.getDrawingBufferSize=function(M){return M.set(a*t,l*t).floor()},this.setDrawingBufferSize=function(M,y,f){a=M,l=y,t=f,$.width=Math.floor(M*f),$.height=Math.floor(y*f),this.setViewport(0,0,M,y)},this.getCurrentViewport=function(M){return M.copy(k)},this.getViewport=function(M){return M.copy(ZJ)},this.setViewport=function(M,y,f,h){if(M.isVector4)ZJ.set(M.x,M.y,M.z,M.w);else ZJ.set(M,y,f,h);GJ.viewport(k.copy(ZJ).multiplyScalar(t).round())},this.getScissor=function(M){return M.copy(_J)},this.setScissor=function(M,y,f,h){if(M.isVector4)_J.set(M.x,M.y,M.z,M.w);else _J.set(M,y,f,h);GJ.scissor(T.copy(_J).multiplyScalar(t).round())},this.getScissorTest=function(){return fJ},this.setScissorTest=function(M){GJ.setScissorTest(fJ=M)},this.setOpaqueSort=function(M){g=M},this.setTransparentSort=function(M){XJ=M},this.getClearColor=function(M){return M.copy(FJ.getClearColor())},this.setClearColor=function(){FJ.setClearColor.apply(FJ,arguments)},this.getClearAlpha=function(){return FJ.getClearAlpha()},this.setClearAlpha=function(){FJ.setClearAlpha.apply(FJ,arguments)},this.clear=function(M=!0,y=!0,f=!0){let h=0;if(M){let S=!1;if(P!==null){let QJ=P.texture.format;S=QJ===1033||QJ===1031||QJ===1029}if(S){let QJ=P.texture.type,EJ=QJ===1009||QJ===1014||QJ===1012||QJ===1020||QJ===1017||QJ===1018,NJ=FJ.getClearColor(),OJ=FJ.getClearAlpha(),TJ=NJ.r,vJ=NJ.g,MJ=NJ.b;if(EJ)D[0]=TJ,D[1]=vJ,D[2]=MJ,D[3]=OJ,C.clearBufferuiv(C.COLOR,0,D);else N[0]=TJ,N[1]=vJ,N[2]=MJ,N[3]=OJ,C.clearBufferiv(C.COLOR,0,N)}else h|=C.COLOR_BUFFER_BIT}if(y)h|=C.DEPTH_BUFFER_BIT;if(f)h|=C.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295);C.clear(h)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.dispose=function(){$.removeEventListener("webglcontextlost",s,!1),$.removeEventListener("webglcontextrestored",i,!1),$.removeEventListener("webglcontextcreationerror",VJ,!1),UJ.dispose(),DJ.dispose(),wJ.dispose(),w.dispose(),R.dispose(),r.dispose(),xJ.dispose(),Q0.dispose(),c.dispose(),JJ.dispose(),JJ.removeEventListener("sessionstart",f0),JJ.removeEventListener("sessionend",Z9),G6.stop()};function s(M){M.preventDefault(),console.log("THREE.WebGLRenderer: Context Lost."),_=!0}function i(){console.log("THREE.WebGLRenderer: Context Restored."),_=!1;let M=$0.autoReset,y=$J.enabled,f=$J.autoUpdate,h=$J.needsUpdate,S=$J.type;I(),$0.autoReset=M,$J.enabled=y,$J.autoUpdate=f,$J.needsUpdate=h,$J.type=S}function VJ(M){console.error("THREE.WebGLRenderer: A WebGL context could not be created. Reason: ",M.statusMessage)}function qJ(M){let y=M.target;y.removeEventListener("dispose",qJ),hJ(y)}function hJ(M){W0(M),wJ.remove(M)}function W0(M){let y=wJ.get(M).programs;if(y!==void 0){if(y.forEach(function(f){c.releaseProgram(f)}),M.isShaderMaterial)c.releaseShaderCache(M)}}this.renderBufferDirect=function(M,y,f,h,S,QJ){if(y===null)y=WJ;let EJ=S.isMesh&&S.matrixWorld.determinant()<0,NJ=s$(M,y,f,h,S);GJ.setMaterial(h,EJ);let OJ=f.index,TJ=1;if(h.wireframe===!0){if(OJ=o.getWireframeAttribute(f),OJ===void 0)return;TJ=2}let vJ=f.drawRange,MJ=f.attributes.position,cJ=vJ.start*TJ,tJ=(vJ.start+vJ.count)*TJ;if(QJ!==null)cJ=Math.max(cJ,QJ.start*TJ),tJ=Math.min(tJ,(QJ.start+QJ.count)*TJ);if(OJ!==null)cJ=Math.max(cJ,0),tJ=Math.min(tJ,OJ.count);else if(MJ!==void 0&&MJ!==null)cJ=Math.max(cJ,0),tJ=Math.min(tJ,MJ.count);let eJ=tJ-cJ;if(eJ<0||eJ===1/0)return;xJ.setup(S,h,NJ,f,OJ);let B0,iJ=PJ;if(OJ!==null)B0=j.get(OJ),iJ=RJ,iJ.setIndex(B0);if(S.isMesh)if(h.wireframe===!0)GJ.setLineWidth(h.wireframeLinewidth*pJ()),iJ.setMode(C.LINES);else iJ.setMode(C.TRIANGLES);else if(S.isLine){let BJ=h.linewidth;if(BJ===void 0)BJ=1;if(GJ.setLineWidth(BJ*pJ()),S.isLineSegments)iJ.setMode(C.LINES);else if(S.isLineLoop)iJ.setMode(C.LINE_LOOP);else iJ.setMode(C.LINE_STRIP)}else if(S.isPoints)iJ.setMode(C.POINTS);else if(S.isSprite)iJ.setMode(C.TRIANGLES);if(S.isBatchedMesh)if(S._multiDrawInstances!==null)iJ.renderMultiDrawInstances(S._multiDrawStarts,S._multiDrawCounts,S._multiDrawCount,S._multiDrawInstances);else if(!CJ.get("WEBGL_multi_draw")){let{_multiDrawStarts:BJ,_multiDrawCounts:m0,_multiDrawCount:oJ}=S,S0=OJ?j.get(OJ).bytesPerElement:1,z6=wJ.get(h).currentProgram.getUniforms();for(let A0=0;A0<oJ;A0++)z6.setValue(C,"_gl_DrawID",A0),iJ.render(BJ[A0]/S0,m0[A0])}else iJ.renderMultiDraw(S._multiDrawStarts,S._multiDrawCounts,S._multiDrawCount);else if(S.isInstancedMesh)iJ.renderInstances(cJ,eJ,S.count);else if(f.isInstancedBufferGeometry){let BJ=f._maxInstanceCount!==void 0?f._maxInstanceCount:1/0,m0=Math.min(f.instanceCount,BJ);iJ.renderInstances(cJ,eJ,m0)}else iJ.render(cJ,eJ)};function E0(M,y,f){if(M.transparent===!0&&M.side===2&&M.forceSinglePass===!1)M.side=1,M.needsUpdate=!0,q7(M,y,f),M.side=0,M.needsUpdate=!0,q7(M,y,f),M.side=2;else q7(M,y,f)}this.compile=function(M,y,f=null){if(f===null)f=M;if(V=DJ.get(f),V.init(y),A.push(V),f.traverseVisible(function(S){if(S.isLight&&S.layers.test(y.layers)){if(V.pushLight(S),S.castShadow)V.pushShadow(S)}}),M!==f)M.traverseVisible(function(S){if(S.isLight&&S.layers.test(y.layers)){if(V.pushLight(S),S.castShadow)V.pushShadow(S)}});V.setupLights();let h=new Set;return M.traverse(function(S){if(!(S.isMesh||S.isPoints||S.isLine||S.isSprite))return;let QJ=S.material;if(QJ)if(Array.isArray(QJ))for(let EJ=0;EJ<QJ.length;EJ++){let NJ=QJ[EJ];E0(NJ,f,S),h.add(NJ)}else E0(QJ,f,S),h.add(QJ)}),A.pop(),V=null,h},this.compileAsync=function(M,y,f=null){let h=this.compile(M,y,f);return new Promise((S)=>{function QJ(){if(h.forEach(function(EJ){if(wJ.get(EJ).currentProgram.isReady())h.delete(EJ)}),h.size===0){S(M);return}setTimeout(QJ,10)}if(CJ.get("KHR_parallel_shader_compile")!==null)QJ();else setTimeout(QJ,10)})};let sJ=null;function g0(M){if(sJ)sJ(M)}function f0(){G6.stop()}function Z9(){G6.start()}let G6=new N$;if(G6.setAnimationLoop(g0),typeof self<"u")G6.setContext(self);this.setAnimationLoop=function(M){sJ=M,JJ.setAnimationLoop(M),M===null?G6.stop():G6.start()},JJ.addEventListener("sessionstart",f0),JJ.addEventListener("sessionend",Z9),this.render=function(M,y){if(y!==void 0&&y.isCamera!==!0){console.error("THREE.WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(_===!0)return;if(M.matrixWorldAutoUpdate===!0)M.updateMatrixWorld();if(y.parent===null&&y.matrixWorldAutoUpdate===!0)y.updateMatrixWorld();if(JJ.enabled===!0&&JJ.isPresenting===!0){if(JJ.cameraAutoUpdate===!0)JJ.updateCamera(y);y=JJ.getCamera()}if(M.isScene===!0)M.onBeforeRender(z,M,y,P);if(V=DJ.get(M,A.length),V.init(y),A.push(V),YJ.multiplyMatrices(y.projectionMatrix,y.matrixWorldInverse),n.setFromProjectionMatrix(YJ),zJ=this.localClippingEnabled,e=SJ.init(this.clippingPlanes,zJ),O=UJ.get(M,F.length),O.init(),F.push(O),JJ.enabled===!0&&JJ.isPresenting===!0){let QJ=z.xr.getDepthSensingMesh();if(QJ!==null)Q8(QJ,y,-1/0,z.sortObjects)}if(Q8(M,y,0,z.sortObjects),O.finish(),z.sortObjects===!0)O.sort(g,XJ);if(AJ=JJ.enabled===!1||JJ.isPresenting===!1||JJ.hasDepthSensing()===!1,AJ)FJ.addToRenderList(O,M);if(this.info.render.frame++,e===!0)SJ.beginShadows();let f=V.state.shadowsArray;if($J.render(f,M,y),e===!0)SJ.endShadows();if(this.info.autoReset===!0)this.info.reset();let{opaque:h,transmissive:S}=O;if(V.setupLights(),y.isArrayCamera){let QJ=y.cameras;if(S.length>0)for(let EJ=0,NJ=QJ.length;EJ<NJ;EJ++){let OJ=QJ[EJ];Y9(h,S,M,OJ)}if(AJ)FJ.render(M);for(let EJ=0,NJ=QJ.length;EJ<NJ;EJ++){let OJ=QJ[EJ];W9(O,M,OJ,OJ.viewport)}}else{if(S.length>0)Y9(h,S,M,y);if(AJ)FJ.render(M);W9(O,M,y)}if(P!==null)IJ.updateMultisampleRenderTarget(P),IJ.updateRenderTargetMipmap(P);if(M.isScene===!0)M.onAfterRender(z,M,y);if(xJ.resetDefaultState(),p=-1,B=null,A.pop(),A.length>0){if(V=A[A.length-1],e===!0)SJ.setGlobalState(z.clippingPlanes,V.state.camera)}else V=null;if(F.pop(),F.length>0)O=F[F.length-1];else O=null};function Q8(M,y,f,h){if(M.visible===!1)return;if(M.layers.test(y.layers)){if(M.isGroup)f=M.renderOrder;else if(M.isLOD){if(M.autoUpdate===!0)M.update(y)}else if(M.isLight){if(V.pushLight(M),M.castShadow)V.pushShadow(M)}else if(M.isSprite){if(!M.frustumCulled||n.intersectsSprite(M)){if(h)KJ.setFromMatrixPosition(M.matrixWorld).applyMatrix4(YJ);let EJ=r.update(M),NJ=M.material;if(NJ.visible)O.push(M,EJ,NJ,f,KJ.z,null)}}else if(M.isMesh||M.isLine||M.isPoints){if(!M.frustumCulled||n.intersectsObject(M)){let EJ=r.update(M),NJ=M.material;if(h){if(M.boundingSphere!==void 0){if(M.boundingSphere===null)M.computeBoundingSphere();KJ.copy(M.boundingSphere.center)}else{if(EJ.boundingSphere===null)EJ.computeBoundingSphere();KJ.copy(EJ.boundingSphere.center)}KJ.applyMatrix4(M.matrixWorld).applyMatrix4(YJ)}if(Array.isArray(NJ)){let OJ=EJ.groups;for(let TJ=0,vJ=OJ.length;TJ<vJ;TJ++){let MJ=OJ[TJ],cJ=NJ[MJ.materialIndex];if(cJ&&cJ.visible)O.push(M,EJ,cJ,f,KJ.z,MJ)}}else if(NJ.visible)O.push(M,EJ,NJ,f,KJ.z,null)}}}let QJ=M.children;for(let EJ=0,NJ=QJ.length;EJ<NJ;EJ++)Q8(QJ[EJ],y,f,h)}function W9(M,y,f,h){let{opaque:S,transmissive:QJ,transparent:EJ}=M;if(V.setupLightsView(f),e===!0)SJ.setGlobalState(z.clippingPlanes,f);if(h)GJ.viewport(k.copy(h));if(S.length>0)U7(S,y,f);if(QJ.length>0)U7(QJ,y,f);if(EJ.length>0)U7(EJ,y,f);GJ.buffers.depth.setTest(!0),GJ.buffers.depth.setMask(!0),GJ.buffers.color.setMask(!0),GJ.setPolygonOffset(!1)}function Y9(M,y,f,h){if((f.isScene===!0?f.overrideMaterial:null)!==null)return;if(V.state.transmissionRenderTarget[h.id]===void 0)V.state.transmissionRenderTarget[h.id]=new X6(1,1,{generateMipmaps:!0,type:CJ.has("EXT_color_buffer_half_float")||CJ.has("EXT_color_buffer_float")?1016:1009,minFilter:1008,samples:4,stencilBuffer:W,resolveDepthBuffer:!1,resolveStencilBuffer:!1,colorSpace:dJ.workingColorSpace});let QJ=V.state.transmissionRenderTarget[h.id],EJ=h.viewport||k;QJ.setSize(EJ.z,EJ.w);let NJ=z.getRenderTarget();if(z.setRenderTarget(QJ),z.getClearColor(m),u=z.getClearAlpha(),u<1)z.setClearColor(16777215,0.5);if(z.clear(),AJ)FJ.render(f);let OJ=z.toneMapping;z.toneMapping=0;let TJ=h.viewport;if(h.viewport!==void 0)h.viewport=void 0;if(V.setupLightsView(h),e===!0)SJ.setGlobalState(z.clippingPlanes,h);if(U7(M,f,h),IJ.updateMultisampleRenderTarget(QJ),IJ.updateRenderTargetMipmap(QJ),CJ.has("WEBGL_multisampled_render_to_texture")===!1){let vJ=!1;for(let MJ=0,cJ=y.length;MJ<cJ;MJ++){let tJ=y[MJ],eJ=tJ.object,B0=tJ.geometry,iJ=tJ.material,BJ=tJ.group;if(iJ.side===2&&eJ.layers.test(h.layers)){let m0=iJ.side;iJ.side=1,iJ.needsUpdate=!0,H9(eJ,f,h,B0,iJ,BJ),iJ.side=m0,iJ.needsUpdate=!0,vJ=!0}}if(vJ===!0)IJ.updateMultisampleRenderTarget(QJ),IJ.updateRenderTargetMipmap(QJ)}if(z.setRenderTarget(NJ),z.setClearColor(m,u),TJ!==void 0)h.viewport=TJ;z.toneMapping=OJ}function U7(M,y,f){let h=y.isScene===!0?y.overrideMaterial:null;for(let S=0,QJ=M.length;S<QJ;S++){let EJ=M[S],NJ=EJ.object,OJ=EJ.geometry,TJ=h===null?EJ.material:h,vJ=EJ.group;if(NJ.layers.test(f.layers))H9(NJ,y,f,OJ,TJ,vJ)}}function H9(M,y,f,h,S,QJ){if(M.onBeforeRender(z,y,f,h,S,QJ),M.modelViewMatrix.multiplyMatrices(f.matrixWorldInverse,M.matrixWorld),M.normalMatrix.getNormalMatrix(M.modelViewMatrix),S.onBeforeRender(z,y,f,h,M,QJ),S.transparent===!0&&S.side===2&&S.forceSinglePass===!1)S.side=1,S.needsUpdate=!0,z.renderBufferDirect(f,y,h,S,M,QJ),S.side=0,S.needsUpdate=!0,z.renderBufferDirect(f,y,h,S,M,QJ),S.side=2;else z.renderBufferDirect(f,y,h,S,M,QJ);M.onAfterRender(z,y,f,h,S,QJ)}function q7(M,y,f){if(y.isScene!==!0)y=WJ;let h=wJ.get(M),S=V.state.lights,QJ=V.state.shadowsArray,EJ=S.state.version,NJ=c.getParameters(M,S.state,QJ,y,f),OJ=c.getProgramCacheKey(NJ),TJ=h.programs;if(h.environment=M.isMeshStandardMaterial?y.environment:null,h.fog=y.fog,h.envMap=(M.isMeshStandardMaterial?R:w).get(M.envMap||h.environment),h.envMapRotation=h.environment!==null&&M.envMap===null?y.environmentRotation:M.envMapRotation,TJ===void 0)M.addEventListener("dispose",qJ),TJ=new Map,h.programs=TJ;let vJ=TJ.get(OJ);if(vJ!==void 0){if(h.currentProgram===vJ&&h.lightsStateVersion===EJ)return K9(M,NJ),vJ}else NJ.uniforms=c.getUniforms(M),M.onBeforeCompile(NJ,z),vJ=c.acquireProgram(NJ,OJ),TJ.set(OJ,vJ),h.uniforms=NJ.uniforms;let MJ=h.uniforms;if(!M.isShaderMaterial&&!M.isRawShaderMaterial||M.clipping===!0)MJ.clippingPlanes=SJ.uniform;if(K9(M,NJ),h.needsLights=o$(M),h.lightsStateVersion=EJ,h.needsLights)MJ.ambientLightColor.value=S.state.ambient,MJ.lightProbe.value=S.state.probe,MJ.directionalLights.value=S.state.directional,MJ.directionalLightShadows.value=S.state.directionalShadow,MJ.spotLights.value=S.state.spot,MJ.spotLightShadows.value=S.state.spotShadow,MJ.rectAreaLights.value=S.state.rectArea,MJ.ltc_1.value=S.state.rectAreaLTC1,MJ.ltc_2.value=S.state.rectAreaLTC2,MJ.pointLights.value=S.state.point,MJ.pointLightShadows.value=S.state.pointShadow,MJ.hemisphereLights.value=S.state.hemi,MJ.directionalShadowMap.value=S.state.directionalShadowMap,MJ.directionalShadowMatrix.value=S.state.directionalShadowMatrix,MJ.spotShadowMap.value=S.state.spotShadowMap,MJ.spotLightMatrix.value=S.state.spotLightMatrix,MJ.spotLightMap.value=S.state.spotLightMap,MJ.pointShadowMap.value=S.state.pointShadowMap,MJ.pointShadowMatrix.value=S.state.pointShadowMatrix;return h.currentProgram=vJ,h.uniformsList=null,vJ}function X9(M){if(M.uniformsList===null){let y=M.currentProgram.getUniforms();M.uniformsList=Y7.seqWithValue(y.seq,M.uniforms)}return M.uniformsList}function K9(M,y){let f=wJ.get(M);f.outputColorSpace=y.outputColorSpace,f.batching=y.batching,f.batchingColor=y.batchingColor,f.instancing=y.instancing,f.instancingColor=y.instancingColor,f.instancingMorph=y.instancingMorph,f.skinning=y.skinning,f.morphTargets=y.morphTargets,f.morphNormals=y.morphNormals,f.morphColors=y.morphColors,f.morphTargetsCount=y.morphTargetsCount,f.numClippingPlanes=y.numClippingPlanes,f.numIntersection=y.numClipIntersection,f.vertexAlphas=y.vertexAlphas,f.vertexTangents=y.vertexTangents,f.toneMapping=y.toneMapping}function s$(M,y,f,h,S){if(y.isScene!==!0)y=WJ;IJ.resetTextureUnits();let QJ=y.fog,EJ=h.isMeshStandardMaterial?y.environment:null,NJ=P===null?z.outputColorSpace:P.isXRRenderTarget===!0?P.texture.colorSpace:"srgb-linear",OJ=(h.isMeshStandardMaterial?R:w).get(h.envMap||EJ),TJ=h.vertexColors===!0&&!!f.attributes.color&&f.attributes.color.itemSize===4,vJ=!!f.attributes.tangent&&(!!h.normalMap||h.anisotropy>0),MJ=!!f.morphAttributes.position,cJ=!!f.morphAttributes.normal,tJ=!!f.morphAttributes.color,eJ=0;if(h.toneMapped){if(P===null||P.isXRRenderTarget===!0)eJ=z.toneMapping}let B0=f.morphAttributes.position||f.morphAttributes.normal||f.morphAttributes.color,iJ=B0!==void 0?B0.length:0,BJ=wJ.get(h),m0=V.state.lights;if(e===!0){if(zJ===!0||M!==B){let C0=M===B&&h.id===p;SJ.setState(h,M,C0)}}let oJ=!1;if(h.version===BJ.__version){if(BJ.needsLights&&BJ.lightsStateVersion!==m0.state.version)oJ=!0;else if(BJ.outputColorSpace!==NJ)oJ=!0;else if(S.isBatchedMesh&&BJ.batching===!1)oJ=!0;else if(!S.isBatchedMesh&&BJ.batching===!0)oJ=!0;else if(S.isBatchedMesh&&BJ.batchingColor===!0&&S.colorTexture===null)oJ=!0;else if(S.isBatchedMesh&&BJ.batchingColor===!1&&S.colorTexture!==null)oJ=!0;else if(S.isInstancedMesh&&BJ.instancing===!1)oJ=!0;else if(!S.isInstancedMesh&&BJ.instancing===!0)oJ=!0;else if(S.isSkinnedMesh&&BJ.skinning===!1)oJ=!0;else if(!S.isSkinnedMesh&&BJ.skinning===!0)oJ=!0;else if(S.isInstancedMesh&&BJ.instancingColor===!0&&S.instanceColor===null)oJ=!0;else if(S.isInstancedMesh&&BJ.instancingColor===!1&&S.instanceColor!==null)oJ=!0;else if(S.isInstancedMesh&&BJ.instancingMorph===!0&&S.morphTexture===null)oJ=!0;else if(S.isInstancedMesh&&BJ.instancingMorph===!1&&S.morphTexture!==null)oJ=!0;else if(BJ.envMap!==OJ)oJ=!0;else if(h.fog===!0&&BJ.fog!==QJ)oJ=!0;else if(BJ.numClippingPlanes!==void 0&&(BJ.numClippingPlanes!==SJ.numPlanes||BJ.numIntersection!==SJ.numIntersection))oJ=!0;else if(BJ.vertexAlphas!==TJ)oJ=!0;else if(BJ.vertexTangents!==vJ)oJ=!0;else if(BJ.morphTargets!==MJ)oJ=!0;else if(BJ.morphNormals!==cJ)oJ=!0;else if(BJ.morphColors!==tJ)oJ=!0;else if(BJ.toneMapping!==eJ)oJ=!0;else if(BJ.morphTargetsCount!==iJ)oJ=!0}else oJ=!0,BJ.__version=h.version;let S0=BJ.currentProgram;if(oJ===!0)S0=q7(h,y,S);let z6=!1,A0=!1,s6=!1,J0=S0.getUniforms(),h0=BJ.uniforms;if(GJ.useProgram(S0.program))z6=!0,A0=!0,s6=!0;if(h.id!==p)p=h.id,A0=!0;if(z6||B!==M){if(GJ.buffers.depth.getReversed())kJ.copy(M.projectionMatrix),e$(kJ),J5(kJ),J0.setValue(C,"projectionMatrix",kJ);else J0.setValue(C,"projectionMatrix",M.projectionMatrix);J0.setValue(C,"viewMatrix",M.matrixWorldInverse);let r0=J0.map.cameraPosition;if(r0!==void 0)r0.setValue(C,d.setFromMatrixPosition(M.matrixWorld));if(mJ.logarithmicDepthBuffer)J0.setValue(C,"logDepthBufFC",2/(Math.log(M.far+1)/Math.LN2));if(h.isMeshPhongMaterial||h.isMeshToonMaterial||h.isMeshLambertMaterial||h.isMeshBasicMaterial||h.isMeshStandardMaterial||h.isShaderMaterial)J0.setValue(C,"isOrthographic",M.isOrthographicCamera===!0);if(B!==M)B=M,A0=!0,s6=!0}if(S.isSkinnedMesh){J0.setOptional(C,S,"bindMatrix"),J0.setOptional(C,S,"bindMatrixInverse");let C0=S.skeleton;if(C0){if(C0.boneTexture===null)C0.computeBoneTexture();J0.setValue(C,"boneTexture",C0.boneTexture,IJ)}}if(S.isBatchedMesh){if(J0.setOptional(C,S,"batchingTexture"),J0.setValue(C,"batchingTexture",S._matricesTexture,IJ),J0.setOptional(C,S,"batchingIdTexture"),J0.setValue(C,"batchingIdTexture",S._indirectTexture,IJ),J0.setOptional(C,S,"batchingColorTexture"),S._colorsTexture!==null)J0.setValue(C,"batchingColorTexture",S._colorsTexture,IJ)}let i6=f.morphAttributes;if(i6.position!==void 0||i6.normal!==void 0||i6.color!==void 0)gJ.update(S,f,S0);if(A0||BJ.receiveShadow!==S.receiveShadow)BJ.receiveShadow=S.receiveShadow,J0.setValue(C,"receiveShadow",S.receiveShadow);if(h.isMeshGouraudMaterial&&h.envMap!==null)h0.envMap.value=OJ,h0.flipEnvMap.value=OJ.isCubeTexture&&OJ.isRenderTargetTexture===!1?-1:1;if(h.isMeshStandardMaterial&&h.envMap===null&&y.environment!==null)h0.envMapIntensity.value=y.environmentIntensity;if(A0){if(J0.setValue(C,"toneMappingExposure",z.toneMappingExposure),BJ.needsLights)i$(h0,s6);if(QJ&&h.fog===!0)LJ.refreshFogUniforms(h0,QJ);LJ.refreshMaterialUniforms(h0,h,t,l,V.state.transmissionRenderTarget[M.id]),Y7.upload(C,X9(BJ),h0,IJ)}if(h.isShaderMaterial&&h.uniformsNeedUpdate===!0)Y7.upload(C,X9(BJ),h0,IJ),h.uniformsNeedUpdate=!1;if(h.isSpriteMaterial)J0.setValue(C,"center",S.center);if(J0.setValue(C,"modelViewMatrix",S.modelViewMatrix),J0.setValue(C,"normalMatrix",S.normalMatrix),J0.setValue(C,"modelMatrix",S.matrixWorld),h.isShaderMaterial||h.isRawShaderMaterial){let C0=h.uniformsGroups;for(let r0=0,t0=C0.length;r0<t0;r0++){let G9=C0[r0];Q0.update(G9,S0),Q0.bind(G9,S0)}}return S0}function i$(M,y){M.ambientLightColor.needsUpdate=y,M.lightProbe.needsUpdate=y,M.directionalLights.needsUpdate=y,M.directionalLightShadows.needsUpdate=y,M.pointLights.needsUpdate=y,M.pointLightShadows.needsUpdate=y,M.spotLights.needsUpdate=y,M.spotLightShadows.needsUpdate=y,M.rectAreaLights.needsUpdate=y,M.hemisphereLights.needsUpdate=y}function o$(M){return M.isMeshLambertMaterial||M.isMeshToonMaterial||M.isMeshPhongMaterial||M.isMeshStandardMaterial||M.isShadowMaterial||M.isShaderMaterial&&M.lights===!0}if(this.getActiveCubeFace=function(){return b},this.getActiveMipmapLevel=function(){return L},this.getRenderTarget=function(){return P},this.setRenderTargetTextures=function(M,y,f){wJ.get(M.texture).__webglTexture=y,wJ.get(M.depthTexture).__webglTexture=f;let h=wJ.get(M);if(h.__hasExternalTextures=!0,h.__autoAllocateDepthBuffer=f===void 0,!h.__autoAllocateDepthBuffer){if(CJ.has("WEBGL_multisampled_render_to_texture")===!0)console.warn("THREE.WebGLRenderer: Render-to-texture extension was disabled because an external texture was provided"),h.__useRenderToTexture=!1}},this.setRenderTargetFramebuffer=function(M,y){let f=wJ.get(M);f.__webglFramebuffer=y,f.__useDefaultFramebuffer=y===void 0},this.setRenderTarget=function(M,y=0,f=0){P=M,b=y,L=f;let h=!0,S=null,QJ=!1,EJ=!1;if(M){let OJ=wJ.get(M);if(OJ.__useDefaultFramebuffer!==void 0)GJ.bindFramebuffer(C.FRAMEBUFFER,null),h=!1;else if(OJ.__webglFramebuffer===void 0)IJ.setupRenderTarget(M);else if(OJ.__hasExternalTextures)IJ.rebindTextures(M,wJ.get(M.texture).__webglTexture,wJ.get(M.depthTexture).__webglTexture);else if(M.depthBuffer){let MJ=M.depthTexture;if(OJ.__boundDepthTexture!==MJ){if(MJ!==null&&wJ.has(MJ)&&(M.width!==MJ.image.width||M.height!==MJ.image.height))throw Error("WebGLRenderTarget: Attached DepthTexture is initialized to the incorrect size.");IJ.setupDepthRenderbuffer(M)}}let TJ=M.texture;if(TJ.isData3DTexture||TJ.isDataArrayTexture||TJ.isCompressedArrayTexture)EJ=!0;let vJ=wJ.get(M).__webglFramebuffer;if(M.isWebGLCubeRenderTarget){if(Array.isArray(vJ[y]))S=vJ[y][f];else S=vJ[y];QJ=!0}else if(M.samples>0&&IJ.useMultisampledRTT(M)===!1)S=wJ.get(M).__webglMultisampledFramebuffer;else if(Array.isArray(vJ))S=vJ[f];else S=vJ;k.copy(M.viewport),T.copy(M.scissor),x=M.scissorTest}else k.copy(ZJ).multiplyScalar(t).floor(),T.copy(_J).multiplyScalar(t).floor(),x=fJ;if(GJ.bindFramebuffer(C.FRAMEBUFFER,S)&&h)GJ.drawBuffers(M,S);if(GJ.viewport(k),GJ.scissor(T),GJ.setScissorTest(x),QJ){let OJ=wJ.get(M.texture);C.framebufferTexture2D(C.FRAMEBUFFER,C.COLOR_ATTACHMENT0,C.TEXTURE_CUBE_MAP_POSITIVE_X+y,OJ.__webglTexture,f)}else if(EJ){let OJ=wJ.get(M.texture),TJ=y||0;C.framebufferTextureLayer(C.FRAMEBUFFER,C.COLOR_ATTACHMENT0,OJ.__webglTexture,f||0,TJ)}p=-1},this.readRenderTargetPixels=function(M,y,f,h,S,QJ,EJ){if(!(M&&M.isWebGLRenderTarget)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let NJ=wJ.get(M).__webglFramebuffer;if(M.isWebGLCubeRenderTarget&&EJ!==void 0)NJ=NJ[EJ];if(NJ){GJ.bindFramebuffer(C.FRAMEBUFFER,NJ);try{let OJ=M.texture,TJ=OJ.format,vJ=OJ.type;if(!mJ.textureFormatReadable(TJ)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(!mJ.textureTypeReadable(vJ)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}if(y>=0&&y<=M.width-h&&(f>=0&&f<=M.height-S))C.readPixels(y,f,h,S,yJ.convert(TJ),yJ.convert(vJ),QJ)}finally{let OJ=P!==null?wJ.get(P).__webglFramebuffer:null;GJ.bindFramebuffer(C.FRAMEBUFFER,OJ)}}},this.readRenderTargetPixelsAsync=async function(M,y,f,h,S,QJ,EJ){if(!(M&&M.isWebGLRenderTarget))throw Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let NJ=wJ.get(M).__webglFramebuffer;if(M.isWebGLCubeRenderTarget&&EJ!==void 0)NJ=NJ[EJ];if(NJ){let OJ=M.texture,TJ=OJ.format,vJ=OJ.type;if(!mJ.textureFormatReadable(TJ))throw Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(!mJ.textureTypeReadable(vJ))throw Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");if(y>=0&&y<=M.width-h&&(f>=0&&f<=M.height-S)){GJ.bindFramebuffer(C.FRAMEBUFFER,NJ);let MJ=C.createBuffer();C.bindBuffer(C.PIXEL_PACK_BUFFER,MJ),C.bufferData(C.PIXEL_PACK_BUFFER,QJ.byteLength,C.STREAM_READ),C.readPixels(y,f,h,S,yJ.convert(TJ),yJ.convert(vJ),0);let cJ=P!==null?wJ.get(P).__webglFramebuffer:null;GJ.bindFramebuffer(C.FRAMEBUFFER,cJ);let tJ=C.fenceSync(C.SYNC_GPU_COMMANDS_COMPLETE,0);return C.flush(),await t$(C,tJ,4),C.bindBuffer(C.PIXEL_PACK_BUFFER,MJ),C.getBufferSubData(C.PIXEL_PACK_BUFFER,0,QJ),C.deleteBuffer(MJ),C.deleteSync(tJ),QJ}else throw Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")}},this.copyFramebufferToTexture=function(M,y=null,f=0){if(M.isTexture!==!0)Z7("WebGLRenderer: copyFramebufferToTexture function signature has changed."),y=arguments[0]||null,M=arguments[1];let h=Math.pow(2,-f),S=Math.floor(M.image.width*h),QJ=Math.floor(M.image.height*h),EJ=y!==null?y.x:0,NJ=y!==null?y.y:0;IJ.setTexture2D(M,0),C.copyTexSubImage2D(C.TEXTURE_2D,f,0,0,EJ,NJ,S,QJ),GJ.unbindTexture()},this.copyTextureToTexture=function(M,y,f=null,h=null,S=0){if(M.isTexture!==!0)Z7("WebGLRenderer: copyTextureToTexture function signature has changed."),h=arguments[0]||null,M=arguments[1],y=arguments[2],S=arguments[3]||0,f=null;let QJ,EJ,NJ,OJ,TJ,vJ,MJ,cJ,tJ,eJ=M.isCompressedTexture?M.mipmaps[S]:M.image;if(f!==null)QJ=f.max.x-f.min.x,EJ=f.max.y-f.min.y,NJ=f.isBox3?f.max.z-f.min.z:1,OJ=f.min.x,TJ=f.min.y,vJ=f.isBox3?f.min.z:0;else QJ=eJ.width,EJ=eJ.height,NJ=eJ.depth||1,OJ=0,TJ=0,vJ=0;if(h!==null)MJ=h.x,cJ=h.y,tJ=h.z;else MJ=0,cJ=0,tJ=0;let B0=yJ.convert(y.format),iJ=yJ.convert(y.type),BJ;if(y.isData3DTexture)IJ.setTexture3D(y,0),BJ=C.TEXTURE_3D;else if(y.isDataArrayTexture||y.isCompressedArrayTexture)IJ.setTexture2DArray(y,0),BJ=C.TEXTURE_2D_ARRAY;else IJ.setTexture2D(y,0),BJ=C.TEXTURE_2D;C.pixelStorei(C.UNPACK_FLIP_Y_WEBGL,y.flipY),C.pixelStorei(C.UNPACK_PREMULTIPLY_ALPHA_WEBGL,y.premultiplyAlpha),C.pixelStorei(C.UNPACK_ALIGNMENT,y.unpackAlignment);let m0=C.getParameter(C.UNPACK_ROW_LENGTH),oJ=C.getParameter(C.UNPACK_IMAGE_HEIGHT),S0=C.getParameter(C.UNPACK_SKIP_PIXELS),z6=C.getParameter(C.UNPACK_SKIP_ROWS),A0=C.getParameter(C.UNPACK_SKIP_IMAGES);C.pixelStorei(C.UNPACK_ROW_LENGTH,eJ.width),C.pixelStorei(C.UNPACK_IMAGE_HEIGHT,eJ.height),C.pixelStorei(C.UNPACK_SKIP_PIXELS,OJ),C.pixelStorei(C.UNPACK_SKIP_ROWS,TJ),C.pixelStorei(C.UNPACK_SKIP_IMAGES,vJ);let s6=M.isDataArrayTexture||M.isData3DTexture,J0=y.isDataArrayTexture||y.isData3DTexture;if(M.isRenderTargetTexture||M.isDepthTexture){let h0=wJ.get(M),i6=wJ.get(y),C0=wJ.get(h0.__renderTarget),r0=wJ.get(i6.__renderTarget);GJ.bindFramebuffer(C.READ_FRAMEBUFFER,C0.__webglFramebuffer),GJ.bindFramebuffer(C.DRAW_FRAMEBUFFER,r0.__webglFramebuffer);for(let t0=0;t0<NJ;t0++){if(s6)C.framebufferTextureLayer(C.READ_FRAMEBUFFER,C.COLOR_ATTACHMENT0,wJ.get(M).__webglTexture,S,vJ+t0);if(M.isDepthTexture){if(J0)C.framebufferTextureLayer(C.DRAW_FRAMEBUFFER,C.COLOR_ATTACHMENT0,wJ.get(y).__webglTexture,S,tJ+t0);C.blitFramebuffer(OJ,TJ,QJ,EJ,MJ,cJ,QJ,EJ,C.DEPTH_BUFFER_BIT,C.NEAREST)}else if(J0)C.copyTexSubImage3D(BJ,S,MJ,cJ,tJ+t0,OJ,TJ,QJ,EJ);else C.copyTexSubImage2D(BJ,S,MJ,cJ,tJ+t0,OJ,TJ,QJ,EJ)}GJ.bindFramebuffer(C.READ_FRAMEBUFFER,null),GJ.bindFramebuffer(C.DRAW_FRAMEBUFFER,null)}else if(J0)if(M.isDataTexture||M.isData3DTexture)C.texSubImage3D(BJ,S,MJ,cJ,tJ,QJ,EJ,NJ,B0,iJ,eJ.data);else if(y.isCompressedArrayTexture)C.compressedTexSubImage3D(BJ,S,MJ,cJ,tJ,QJ,EJ,NJ,B0,eJ.data);else C.texSubImage3D(BJ,S,MJ,cJ,tJ,QJ,EJ,NJ,B0,iJ,eJ);else if(M.isDataTexture)C.texSubImage2D(C.TEXTURE_2D,S,MJ,cJ,QJ,EJ,B0,iJ,eJ.data);else if(M.isCompressedTexture)C.compressedTexSubImage2D(C.TEXTURE_2D,S,MJ,cJ,eJ.width,eJ.height,B0,eJ.data);else C.texSubImage2D(C.TEXTURE_2D,S,MJ,cJ,QJ,EJ,B0,iJ,eJ);if(C.pixelStorei(C.UNPACK_ROW_LENGTH,m0),C.pixelStorei(C.UNPACK_IMAGE_HEIGHT,oJ),C.pixelStorei(C.UNPACK_SKIP_PIXELS,S0),C.pixelStorei(C.UNPACK_SKIP_ROWS,z6),C.pixelStorei(C.UNPACK_SKIP_IMAGES,A0),S===0&&y.generateMipmaps)C.generateMipmap(BJ);GJ.unbindTexture()},this.copyTextureToTexture3D=function(M,y,f=null,h=null,S=0){if(M.isTexture!==!0)Z7("WebGLRenderer: copyTextureToTexture3D function signature has changed."),f=arguments[0]||null,h=arguments[1]||null,M=arguments[2],y=arguments[3],S=arguments[4]||0;return Z7('WebGLRenderer: copyTextureToTexture3D function has been deprecated. Use "copyTextureToTexture" instead.'),this.copyTextureToTexture(M,y,f,h,S)},this.initRenderTarget=function(M){if(wJ.get(M).__webglFramebuffer===void 0)IJ.setupRenderTarget(M)},this.initTexture=function(M){if(M.isCubeTexture)IJ.setTextureCube(M,0);else if(M.isData3DTexture)IJ.setTexture3D(M,0);else if(M.isDataArrayTexture||M.isCompressedArrayTexture)IJ.setTexture2DArray(M,0);else IJ.setTexture2D(M,0);GJ.unbindTexture()},this.resetState=function(){b=0,L=0,P=null,GJ.reset(),xJ.reset()},typeof __THREE_DEVTOOLS__<"u")__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return 2000}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(J){this._outputColorSpace=J;let $=this.getContext();$.drawingBufferColorspace=dJ._getDrawingBufferColorSpace(J),$.unpackColorSpace=dJ._getUnpackColorSpace()}}class i8 extends R0{constructor(){super();if(this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new o0,this.environmentIntensity=1,this.environmentRotation=new o0,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u")__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(J,$){if(super.copy(J,$),J.background!==null)this.background=J.background.clone();if(J.environment!==null)this.environment=J.environment.clone();if(J.fog!==null)this.fog=J.fog.clone();if(this.backgroundBlurriness=J.backgroundBlurriness,this.backgroundIntensity=J.backgroundIntensity,this.backgroundRotation.copy(J.backgroundRotation),this.environmentIntensity=J.environmentIntensity,this.environmentRotation.copy(J.environmentRotation),J.overrideMaterial!==null)this.overrideMaterial=J.overrideMaterial.clone();return this.matrixAutoUpdate=J.matrixAutoUpdate,this}toJSON(J){let $=super.toJSON(J);if(this.fog!==null)$.object.fog=this.fog.toJSON();if(this.backgroundBlurriness>0)$.object.backgroundBlurriness=this.backgroundBlurriness;if(this.backgroundIntensity!==1)$.object.backgroundIntensity=this.backgroundIntensity;if($.object.backgroundRotation=this.backgroundRotation.toArray(),this.environmentIntensity!==1)$.object.environmentIntensity=this.environmentIntensity;return $.object.environmentRotation=this.environmentRotation.toArray(),$}}class v${constructor(J,$){this.isInterleavedBuffer=!0,this.array=J,this.stride=$,this.count=J!==void 0?J.length/$:0,this.usage=35044,this.updateRanges=[],this.version=0,this.uuid=H6()}onUploadCallback(){}set needsUpdate(J){if(J===!0)this.version++}setUsage(J){return this.usage=J,this}addUpdateRange(J,$){this.updateRanges.push({start:J,count:$})}clearUpdateRanges(){this.updateRanges.length=0}copy(J){return this.array=new J.array.constructor(J.array),this.count=J.count,this.stride=J.stride,this.usage=J.usage,this}copyAt(J,$,Q){J*=this.stride,Q*=$.stride;for(let Z=0,W=this.stride;Z<W;Z++)this.array[J+Z]=$.array[Q+Z];return this}set(J,$=0){return this.array.set(J,$),this}clone(J){if(J.arrayBuffers===void 0)J.arrayBuffers={};if(this.array.buffer._uuid===void 0)this.array.buffer._uuid=H6();if(J.arrayBuffers[this.array.buffer._uuid]===void 0)J.arrayBuffers[this.array.buffer._uuid]=this.array.slice(0).buffer;let $=new this.array.constructor(J.arrayBuffers[this.array.buffer._uuid]),Q=new this.constructor($,this.stride);return Q.setUsage(this.usage),Q}onUpload(J){return this.onUploadCallback=J,this}toJSON(J){if(J.arrayBuffers===void 0)J.arrayBuffers={};if(this.array.buffer._uuid===void 0)this.array.buffer._uuid=H6();if(J.arrayBuffers[this.array.buffer._uuid]===void 0)J.arrayBuffers[this.array.buffer._uuid]=Array.from(new Uint32Array(this.array.buffer));return{uuid:this.uuid,buffer:this.array.buffer._uuid,type:this.array.constructor.name,stride:this.stride}}}var N0=new v;class n7{constructor(J,$,Q,Z=!1){this.isInterleavedBufferAttribute=!0,this.name="",this.data=J,this.itemSize=$,this.offset=Q,this.normalized=Z}get count(){return this.data.count}get array(){return this.data.array}set needsUpdate(J){this.data.needsUpdate=J}applyMatrix4(J){for(let $=0,Q=this.data.count;$<Q;$++)N0.fromBufferAttribute(this,$),N0.applyMatrix4(J),this.setXYZ($,N0.x,N0.y,N0.z);return this}applyNormalMatrix(J){for(let $=0,Q=this.count;$<Q;$++)N0.fromBufferAttribute(this,$),N0.applyNormalMatrix(J),this.setXYZ($,N0.x,N0.y,N0.z);return this}transformDirection(J){for(let $=0,Q=this.count;$<Q;$++)N0.fromBufferAttribute(this,$),N0.transformDirection(J),this.setXYZ($,N0.x,N0.y,N0.z);return this}getComponent(J,$){let Q=this.array[J*this.data.stride+this.offset+$];if(this.normalized)Q=x0(Q,this.array);return Q}setComponent(J,$,Q){if(this.normalized)Q=aJ(Q,this.array);return this.data.array[J*this.data.stride+this.offset+$]=Q,this}setX(J,$){if(this.normalized)$=aJ($,this.array);return this.data.array[J*this.data.stride+this.offset]=$,this}setY(J,$){if(this.normalized)$=aJ($,this.array);return this.data.array[J*this.data.stride+this.offset+1]=$,this}setZ(J,$){if(this.normalized)$=aJ($,this.array);return this.data.array[J*this.data.stride+this.offset+2]=$,this}setW(J,$){if(this.normalized)$=aJ($,this.array);return this.data.array[J*this.data.stride+this.offset+3]=$,this}getX(J){let $=this.data.array[J*this.data.stride+this.offset];if(this.normalized)$=x0($,this.array);return $}getY(J){let $=this.data.array[J*this.data.stride+this.offset+1];if(this.normalized)$=x0($,this.array);return $}getZ(J){let $=this.data.array[J*this.data.stride+this.offset+2];if(this.normalized)$=x0($,this.array);return $}getW(J){let $=this.data.array[J*this.data.stride+this.offset+3];if(this.normalized)$=x0($,this.array);return $}setXY(J,$,Q){if(J=J*this.data.stride+this.offset,this.normalized)$=aJ($,this.array),Q=aJ(Q,this.array);return this.data.array[J+0]=$,this.data.array[J+1]=Q,this}setXYZ(J,$,Q,Z){if(J=J*this.data.stride+this.offset,this.normalized)$=aJ($,this.array),Q=aJ(Q,this.array),Z=aJ(Z,this.array);return this.data.array[J+0]=$,this.data.array[J+1]=Q,this.data.array[J+2]=Z,this}setXYZW(J,$,Q,Z,W){if(J=J*this.data.stride+this.offset,this.normalized)$=aJ($,this.array),Q=aJ(Q,this.array),Z=aJ(Z,this.array),W=aJ(W,this.array);return this.data.array[J+0]=$,this.data.array[J+1]=Q,this.data.array[J+2]=Z,this.data.array[J+3]=W,this}clone(J){if(J===void 0){console.log("THREE.InterleavedBufferAttribute.clone(): Cloning an interleaved buffer attribute will de-interleave buffer data.");let $=[];for(let Q=0;Q<this.count;Q++){let Z=Q*this.data.stride+this.offset;for(let W=0;W<this.itemSize;W++)$.push(this.data.array[Z+W])}return new I0(new this.array.constructor($),this.itemSize,this.normalized)}else{if(J.interleavedBuffers===void 0)J.interleavedBuffers={};if(J.interleavedBuffers[this.data.uuid]===void 0)J.interleavedBuffers[this.data.uuid]=this.data.clone(J);return new n7(J.interleavedBuffers[this.data.uuid],this.itemSize,this.offset,this.normalized)}}toJSON(J){if(J===void 0){console.log("THREE.InterleavedBufferAttribute.toJSON(): Serializing an interleaved buffer attribute will de-interleave buffer data.");let $=[];for(let Q=0;Q<this.count;Q++){let Z=Q*this.data.stride+this.offset;for(let W=0;W<this.itemSize;W++)$.push(this.data.array[Z+W])}return{itemSize:this.itemSize,type:this.array.constructor.name,array:$,normalized:this.normalized}}else{if(J.interleavedBuffers===void 0)J.interleavedBuffers={};if(J.interleavedBuffers[this.data.uuid]===void 0)J.interleavedBuffers[this.data.uuid]=this.data.toJSON(J);return{isInterleavedBufferAttribute:!0,itemSize:this.itemSize,data:this.data.uuid,offset:this.offset,normalized:this.normalized}}}}class t7 extends K6{static get type(){return"SpriteMaterial"}constructor(J){super();this.isSpriteMaterial=!0,this.color=new nJ(16777215),this.map=null,this.alphaMap=null,this.rotation=0,this.sizeAttenuation=!0,this.transparent=!0,this.fog=!0,this.setValues(J)}copy(J){return super.copy(J),this.color.copy(J.color),this.map=J.map,this.alphaMap=J.alphaMap,this.rotation=J.rotation,this.sizeAttenuation=J.sizeAttenuation,this.fog=J.fog,this}}var f6,e6=new v,h6=new v,b6=new v,x6=new uJ,J7=new uJ,j$=new Z0,y7=new v,$7=new v,v7=new v,J$=new uJ,I8=new uJ,$$=new uJ;class o8 extends R0{constructor(J=new t7){super();if(this.isSprite=!0,this.type="Sprite",f6===void 0){f6=new V0;let $=new Float32Array([-0.5,-0.5,0,0,0,0.5,-0.5,0,1,0,0.5,0.5,0,1,1,-0.5,0.5,0,0,1]),Q=new v$($,5);f6.setIndex([0,1,2,0,2,3]),f6.setAttribute("position",new n7(Q,3,0,!1)),f6.setAttribute("uv",new n7(Q,2,3,!1))}this.geometry=f6,this.material=J,this.center=new uJ(0.5,0.5)}raycast(J,$){if(J.camera===null)console.error('THREE.Sprite: "Raycaster.camera" needs to be set in order to raycast against sprites.');if(h6.setFromMatrixScale(this.matrixWorld),j$.copy(J.camera.matrixWorld),this.modelViewMatrix.multiplyMatrices(J.camera.matrixWorldInverse,this.matrixWorld),b6.setFromMatrixPosition(this.modelViewMatrix),J.camera.isPerspectiveCamera&&this.material.sizeAttenuation===!1)h6.multiplyScalar(-b6.z);let Q=this.material.rotation,Z,W;if(Q!==0)W=Math.cos(Q),Z=Math.sin(Q);let Y=this.center;j7(y7.set(-0.5,-0.5,0),b6,Y,h6,Z,W),j7($7.set(0.5,-0.5,0),b6,Y,h6,Z,W),j7(v7.set(0.5,0.5,0),b6,Y,h6,Z,W),J$.set(0,0),I8.set(1,0),$$.set(1,1);let X=J.ray.intersectTriangle(y7,$7,v7,!1,e6);if(X===null){if(j7($7.set(-0.5,0.5,0),b6,Y,h6,Z,W),I8.set(0,1),X=J.ray.intersectTriangle(y7,v7,$7,!1,e6),X===null)return}let H=J.ray.origin.distanceTo(e6);if(H<J.near||H>J.far)return;$.push({distance:H,point:e6.clone(),uv:_0.getInterpolation(e6,y7,$7,v7,J$,I8,$$,new uJ),face:null,object:this})}copy(J,$){if(super.copy(J,$),J.center!==void 0)this.center.copy(J.center);return this.material=J.material,this}}function j7(J,$,Q,Z,W,Y){if(x6.subVectors(J,Q).addScalar(0.5).multiply(Z),W!==void 0)J7.x=Y*x6.x-W*x6.y,J7.y=W*x6.x+Y*x6.y;else J7.copy(x6);J.copy($),J.x+=J7.x,J.y+=J7.y,J.applyMatrix4(j$)}class X7 extends K6{static get type(){return"LineBasicMaterial"}constructor(J){super();this.isLineBasicMaterial=!0,this.color=new nJ(16777215),this.map=null,this.linewidth=1,this.linecap="round",this.linejoin="round",this.fog=!0,this.setValues(J)}copy(J){return super.copy(J),this.color.copy(J.color),this.map=J.map,this.linewidth=J.linewidth,this.linecap=J.linecap,this.linejoin=J.linejoin,this.fog=J.fog,this}}var s7=new v,i7=new v,Q$=new Z0,Q7=new o7,f7=new l6,S8=new v,Z$=new v;class f$ extends R0{constructor(J=new V0,$=new X7){super();this.isLine=!0,this.type="Line",this.geometry=J,this.material=$,this.updateMorphTargets()}copy(J,$){return super.copy(J,$),this.material=Array.isArray(J.material)?J.material.slice():J.material,this.geometry=J.geometry,this}computeLineDistances(){let J=this.geometry;if(J.index===null){let $=J.attributes.position,Q=[0];for(let Z=1,W=$.count;Z<W;Z++)s7.fromBufferAttribute($,Z-1),i7.fromBufferAttribute($,Z),Q[Z]=Q[Z-1],Q[Z]+=s7.distanceTo(i7);J.setAttribute("lineDistance",new Y0(Q,1))}else console.warn("THREE.Line.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}raycast(J,$){let Q=this.geometry,Z=this.matrixWorld,W=J.params.Line.threshold,Y=Q.drawRange;if(Q.boundingSphere===null)Q.computeBoundingSphere();if(f7.copy(Q.boundingSphere),f7.applyMatrix4(Z),f7.radius+=W,J.ray.intersectsSphere(f7)===!1)return;Q$.copy(Z).invert(),Q7.copy(J.ray).applyMatrix4(Q$);let X=W/((this.scale.x+this.scale.y+this.scale.z)/3),H=X*X,K=this.isLineSegments?2:1,G=Q.index,U=Q.attributes.position;if(G!==null){let q=Math.max(0,Y.start),D=Math.min(G.count,Y.start+Y.count);for(let N=q,O=D-1;N<O;N+=K){let V=G.getX(N),F=G.getX(N+1),A=h7(this,J,Q7,H,V,F);if(A)$.push(A)}if(this.isLineLoop){let N=G.getX(D-1),O=G.getX(q),V=h7(this,J,Q7,H,N,O);if(V)$.push(V)}}else{let q=Math.max(0,Y.start),D=Math.min(U.count,Y.start+Y.count);for(let N=q,O=D-1;N<O;N+=K){let V=h7(this,J,Q7,H,N,N+1);if(V)$.push(V)}if(this.isLineLoop){let N=h7(this,J,Q7,H,D-1,q);if(N)$.push(N)}}}updateMorphTargets(){let $=this.geometry.morphAttributes,Q=Object.keys($);if(Q.length>0){let Z=$[Q[0]];if(Z!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let W=0,Y=Z.length;W<Y;W++){let X=Z[W].name||String(W);this.morphTargetInfluences.push(0),this.morphTargetDictionary[X]=W}}}}}function h7(J,$,Q,Z,W,Y){let X=J.geometry.attributes.position;if(s7.fromBufferAttribute(X,W),i7.fromBufferAttribute(X,Y),Q.distanceSqToSegment(s7,i7,S8,Z$)>Z)return;S8.applyMatrix4(J.matrixWorld);let K=$.ray.origin.distanceTo(S8);if(K<$.near||K>$.far)return;return{distance:K,point:Z$.clone().applyMatrix4(J.matrixWorld),index:W,face:null,faceIndex:null,barycoord:null,object:J}}var W$=new v,Y$=new v;class e7 extends f${constructor(J,$){super(J,$);this.isLineSegments=!0,this.type="LineSegments"}computeLineDistances(){let J=this.geometry;if(J.index===null){let $=J.attributes.position,Q=[];for(let Z=0,W=$.count;Z<W;Z+=2)W$.fromBufferAttribute($,Z),Y$.fromBufferAttribute($,Z+1),Q[Z]=Z===0?0:Q[Z-1],Q[Z+1]=Q[Z]+W$.distanceTo(Y$);J.setAttribute("lineDistance",new Y0(Q,1))}else console.warn("THREE.LineSegments.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}}class J8 extends K6{static get type(){return"PointsMaterial"}constructor(J){super();this.isPointsMaterial=!0,this.color=new nJ(16777215),this.map=null,this.alphaMap=null,this.size=1,this.sizeAttenuation=!0,this.fog=!0,this.setValues(J)}copy(J){return super.copy(J),this.color.copy(J.color),this.map=J.map,this.alphaMap=J.alphaMap,this.size=J.size,this.sizeAttenuation=J.sizeAttenuation,this.fog=J.fog,this}}var H$=new Z0,h8=new o7,b7=new l6,x7=new v;class a8 extends R0{constructor(J=new V0,$=new J8){super();this.isPoints=!0,this.type="Points",this.geometry=J,this.material=$,this.updateMorphTargets()}copy(J,$){return super.copy(J,$),this.material=Array.isArray(J.material)?J.material.slice():J.material,this.geometry=J.geometry,this}raycast(J,$){let Q=this.geometry,Z=this.matrixWorld,W=J.params.Points.threshold,Y=Q.drawRange;if(Q.boundingSphere===null)Q.computeBoundingSphere();if(b7.copy(Q.boundingSphere),b7.applyMatrix4(Z),b7.radius+=W,J.ray.intersectsSphere(b7)===!1)return;H$.copy(Z).invert(),h8.copy(J.ray).applyMatrix4(H$);let X=W/((this.scale.x+this.scale.y+this.scale.z)/3),H=X*X,K=Q.index,E=Q.attributes.position;if(K!==null){let U=Math.max(0,Y.start),q=Math.min(K.count,Y.start+Y.count);for(let D=U,N=q;D<N;D++){let O=K.getX(D);x7.fromBufferAttribute(E,O),X$(x7,O,H,Z,J,$,this)}}else{let U=Math.max(0,Y.start),q=Math.min(E.count,Y.start+Y.count);for(let D=U,N=q;D<N;D++)x7.fromBufferAttribute(E,D),X$(x7,D,H,Z,J,$,this)}}updateMorphTargets(){let $=this.geometry.morphAttributes,Q=Object.keys($);if(Q.length>0){let Z=$[Q[0]];if(Z!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let W=0,Y=Z.length;W<Y;W++){let X=Z[W].name||String(W);this.morphTargetInfluences.push(0),this.morphTargetDictionary[X]=W}}}}}function X$(J,$,Q,Z,W,Y,X){let H=h8.distanceSqToPoint(J);if(H<Q){let K=new v;h8.closestPointToPoint(J,K),K.applyMatrix4(Z);let G=W.ray.origin.distanceTo(K);if(G<W.near||G>W.far)return;Y.push({distance:G,distanceToRay:Math.sqrt(H),point:K,index:$,face:null,faceIndex:null,barycoord:null,object:X})}}class r8 extends M0{constructor(J,$,Q,Z,W,Y,X,H,K){super(J,$,Q,Z,W,Y,X,H,K);this.isCanvasTexture=!0,this.needsUpdate=!0}}class $8 extends V0{constructor(J=1,$=1,Q=1,Z=32,W=1,Y=!1,X=0,H=Math.PI*2){super();this.type="CylinderGeometry",this.parameters={radiusTop:J,radiusBottom:$,height:Q,radialSegments:Z,heightSegments:W,openEnded:Y,thetaStart:X,thetaLength:H};let K=this;Z=Math.floor(Z),W=Math.floor(W);let G=[],E=[],U=[],q=[],D=0,N=[],O=Q/2,V=0;if(F(),Y===!1){if(J>0)A(!0);if($>0)A(!1)}this.setIndex(G),this.setAttribute("position",new Y0(E,3)),this.setAttribute("normal",new Y0(U,3)),this.setAttribute("uv",new Y0(q,2));function F(){let z=new v,_=new v,b=0,L=($-J)/Q;for(let P=0;P<=W;P++){let p=[],B=P/W,k=B*($-J)+J;for(let T=0;T<=Z;T++){let x=T/Z,m=x*H+X,u=Math.sin(m),a=Math.cos(m);_.x=k*u,_.y=-B*Q+O,_.z=k*a,E.push(_.x,_.y,_.z),z.set(u,L,a).normalize(),U.push(z.x,z.y,z.z),q.push(x,1-B),p.push(D++)}N.push(p)}for(let P=0;P<Z;P++)for(let p=0;p<W;p++){let B=N[p][P],k=N[p+1][P],T=N[p+1][P+1],x=N[p][P+1];if(J>0||p!==0)G.push(B,k,x),b+=3;if($>0||p!==W-1)G.push(k,T,x),b+=3}K.addGroup(V,b,0),V+=b}function A(z){let _=D,b=new uJ,L=new v,P=0,p=z===!0?J:$,B=z===!0?1:-1;for(let T=1;T<=Z;T++)E.push(0,O*B,0),U.push(0,B,0),q.push(0.5,0.5),D++;let k=D;for(let T=0;T<=Z;T++){let m=T/Z*H+X,u=Math.cos(m),a=Math.sin(m);L.x=p*a,L.y=O*B,L.z=p*u,E.push(L.x,L.y,L.z),U.push(0,B,0),b.x=u*0.5+0.5,b.y=a*0.5*B+0.5,q.push(b.x,b.y),D++}for(let T=0;T<Z;T++){let x=_+T,m=k+T;if(z===!0)G.push(m,m+1,x);else G.push(m+1,m,x);P+=3}K.addGroup(V,P,z===!0?1:2),V+=P}}copy(J){return super.copy(J),this.parameters=Object.assign({},J.parameters),this}static fromJSON(J){return new $8(J.radiusTop,J.radiusBottom,J.height,J.radialSegments,J.heightSegments,J.openEnded,J.thetaStart,J.thetaLength)}}var p7=new v,g7=new v,y8=new v,m7=new _0;class t8 extends V0{constructor(J=null,$=1){super();if(this.type="EdgesGeometry",this.parameters={geometry:J,thresholdAngle:$},J!==null){let Z=Math.pow(10,4),W=Math.cos(l7*$),Y=J.getIndex(),X=J.getAttribute("position"),H=Y?Y.count:X.count,K=[0,0,0],G=["a","b","c"],E=[,,,],U={},q=[];for(let D=0;D<H;D+=3){if(Y)K[0]=Y.getX(D),K[1]=Y.getX(D+1),K[2]=Y.getX(D+2);else K[0]=D,K[1]=D+1,K[2]=D+2;let{a:N,b:O,c:V}=m7;if(N.fromBufferAttribute(X,K[0]),O.fromBufferAttribute(X,K[1]),V.fromBufferAttribute(X,K[2]),m7.getNormal(y8),E[0]=`${Math.round(N.x*Z)},${Math.round(N.y*Z)},${Math.round(N.z*Z)}`,E[1]=`${Math.round(O.x*Z)},${Math.round(O.y*Z)},${Math.round(O.z*Z)}`,E[2]=`${Math.round(V.x*Z)},${Math.round(V.y*Z)},${Math.round(V.z*Z)}`,E[0]===E[1]||E[1]===E[2]||E[2]===E[0])continue;for(let F=0;F<3;F++){let A=(F+1)%3,z=E[F],_=E[A],b=m7[G[F]],L=m7[G[A]],P=`${z}_${_}`,p=`${_}_${z}`;if(p in U&&U[p]){if(y8.dot(U[p].normal)<=W)q.push(b.x,b.y,b.z),q.push(L.x,L.y,L.z);U[p]=null}else if(!(P in U))U[P]={index0:K[F],index1:K[A],normal:y8.clone()}}}for(let D in U)if(U[D]){let{index0:N,index1:O}=U[D];p7.fromBufferAttribute(X,N),g7.fromBufferAttribute(X,O),q.push(p7.x,p7.y,p7.z),q.push(g7.x,g7.y,g7.z)}this.setAttribute("position",new Y0(q,3))}}copy(J){return super.copy(J),this.parameters=Object.assign({},J.parameters),this}}class K7 extends V0{constructor(J=1,$=32,Q=16,Z=0,W=Math.PI*2,Y=0,X=Math.PI){super();this.type="SphereGeometry",this.parameters={radius:J,widthSegments:$,heightSegments:Q,phiStart:Z,phiLength:W,thetaStart:Y,thetaLength:X},$=Math.max(3,Math.floor($)),Q=Math.max(2,Math.floor(Q));let H=Math.min(Y+X,Math.PI),K=0,G=[],E=new v,U=new v,q=[],D=[],N=[],O=[];for(let V=0;V<=Q;V++){let F=[],A=V/Q,z=0;if(V===0&&Y===0)z=0.5/$;else if(V===Q&&H===Math.PI)z=-0.5/$;for(let _=0;_<=$;_++){let b=_/$;E.x=-J*Math.cos(Z+b*W)*Math.sin(Y+A*X),E.y=J*Math.cos(Y+A*X),E.z=J*Math.sin(Z+b*W)*Math.sin(Y+A*X),D.push(E.x,E.y,E.z),U.copy(E).normalize(),N.push(U.x,U.y,U.z),O.push(b+z,1-A),F.push(K++)}G.push(F)}for(let V=0;V<Q;V++)for(let F=0;F<$;F++){let A=G[V][F+1],z=G[V][F],_=G[V+1][F],b=G[V+1][F+1];if(V!==0||Y>0)q.push(A,z,b);if(V!==Q-1||H<Math.PI)q.push(z,_,b)}this.setIndex(q),this.setAttribute("position",new Y0(D,3)),this.setAttribute("normal",new Y0(N,3)),this.setAttribute("uv",new Y0(O,2))}copy(J){return super.copy(J),this.parameters=Object.assign({},J.parameters),this}static fromJSON(J){return new K7(J.radius,J.widthSegments,J.heightSegments,J.phiStart,J.phiLength,J.thetaStart,J.thetaLength)}}class B6 extends V0{constructor(J=1,$=0.4,Q=12,Z=48,W=Math.PI*2){super();this.type="TorusGeometry",this.parameters={radius:J,tube:$,radialSegments:Q,tubularSegments:Z,arc:W},Q=Math.floor(Q),Z=Math.floor(Z);let Y=[],X=[],H=[],K=[],G=new v,E=new v,U=new v;for(let q=0;q<=Q;q++)for(let D=0;D<=Z;D++){let N=D/Z*W,O=q/Q*Math.PI*2;E.x=(J+$*Math.cos(O))*Math.cos(N),E.y=(J+$*Math.cos(O))*Math.sin(N),E.z=$*Math.sin(O),X.push(E.x,E.y,E.z),G.x=J*Math.cos(N),G.y=J*Math.sin(N),U.subVectors(E,G).normalize(),H.push(U.x,U.y,U.z),K.push(D/Z),K.push(q/Q)}for(let q=1;q<=Q;q++)for(let D=1;D<=Z;D++){let N=(Z+1)*q+D-1,O=(Z+1)*(q-1)+D-1,V=(Z+1)*(q-1)+D,F=(Z+1)*q+D;Y.push(N,O,F),Y.push(O,V,F)}this.setIndex(Y),this.setAttribute("position",new Y0(X,3)),this.setAttribute("normal",new Y0(H,3)),this.setAttribute("uv",new Y0(K,2))}copy(J){return super.copy(J),this.parameters=Object.assign({},J.parameters),this}static fromJSON(J){return new B6(J.radius,J.tube,J.radialSegments,J.tubularSegments,J.arc)}}class e8 extends X7{static get type(){return"LineDashedMaterial"}constructor(J){super();this.isLineDashedMaterial=!0,this.scale=1,this.dashSize=3,this.gapSize=1,this.setValues(J)}copy(J){return super.copy(J),this.scale=J.scale,this.dashSize=J.dashSize,this.gapSize=J.gapSize,this}}function u7(J,$,Q){if(!J||!Q&&J.constructor===$)return J;if(typeof $.BYTES_PER_ELEMENT==="number")return new $(J);return Array.prototype.slice.call(J)}function i4(J){return ArrayBuffer.isView(J)&&!(J instanceof DataView)}class G7{constructor(J,$,Q,Z){this.parameterPositions=J,this._cachedIndex=0,this.resultBuffer=Z!==void 0?Z:new $.constructor(Q),this.sampleValues=$,this.valueSize=Q,this.settings=null,this.DefaultSettings_={}}evaluate(J){let $=this.parameterPositions,Q=this._cachedIndex,Z=$[Q],W=$[Q-1];Q:{J:{let Y;$:{Z:if(!(J<Z)){for(let X=Q+2;;){if(Z===void 0){if(J<W)break Z;return Q=$.length,this._cachedIndex=Q,this.copySampleValue_(Q-1)}if(Q===X)break;if(W=Z,Z=$[++Q],J<Z)break J}Y=$.length;break $}if(!(J>=W)){let X=$[1];if(J<X)Q=2,W=X;for(let H=Q-2;;){if(W===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(Q===H)break;if(Z=W,W=$[--Q-1],J>=W)break J}Y=Q,Q=0;break $}break Q}while(Q<Y){let X=Q+Y>>>1;if(J<$[X])Y=X;else Q=X+1}if(Z=$[Q],W=$[Q-1],W===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(Z===void 0)return Q=$.length,this._cachedIndex=Q,this.copySampleValue_(Q-1)}this._cachedIndex=Q,this.intervalChanged_(Q,W,Z)}return this.interpolate_(Q,W,J,Z)}getSettings_(){return this.settings||this.DefaultSettings_}copySampleValue_(J){let $=this.resultBuffer,Q=this.sampleValues,Z=this.valueSize,W=J*Z;for(let Y=0;Y!==Z;++Y)$[Y]=Q[W+Y];return $}interpolate_(){throw Error("call to abstract method")}intervalChanged_(){}}class h$ extends G7{constructor(J,$,Q,Z){super(J,$,Q,Z);this._weightPrev=-0,this._offsetPrev=-0,this._weightNext=-0,this._offsetNext=-0,this.DefaultSettings_={endingStart:2400,endingEnd:2400}}intervalChanged_(J,$,Q){let Z=this.parameterPositions,W=J-2,Y=J+1,X=Z[W],H=Z[Y];if(X===void 0)switch(this.getSettings_().endingStart){case 2401:W=J,X=2*$-Q;break;case 2402:W=Z.length-2,X=$+Z[W]-Z[W+1];break;default:W=J,X=Q}if(H===void 0)switch(this.getSettings_().endingEnd){case 2401:Y=J,H=2*Q-$;break;case 2402:Y=1,H=Q+Z[1]-Z[0];break;default:Y=J-1,H=$}let K=(Q-$)*0.5,G=this.valueSize;this._weightPrev=K/($-X),this._weightNext=K/(H-Q),this._offsetPrev=W*G,this._offsetNext=Y*G}interpolate_(J,$,Q,Z){let W=this.resultBuffer,Y=this.sampleValues,X=this.valueSize,H=J*X,K=H-X,G=this._offsetPrev,E=this._offsetNext,U=this._weightPrev,q=this._weightNext,D=(Q-$)/(Z-$),N=D*D,O=N*D,V=-U*O+2*U*N-U*D,F=(1+U)*O+(-1.5-2*U)*N+(-0.5+U)*D+1,A=(-1-q)*O+(1.5+q)*N+0.5*D,z=q*O-q*N;for(let _=0;_!==X;++_)W[_]=V*Y[G+_]+F*Y[K+_]+A*Y[H+_]+z*Y[E+_];return W}}class b$ extends G7{constructor(J,$,Q,Z){super(J,$,Q,Z)}interpolate_(J,$,Q,Z){let W=this.resultBuffer,Y=this.sampleValues,X=this.valueSize,H=J*X,K=H-X,G=(Q-$)/(Z-$),E=1-G;for(let U=0;U!==X;++U)W[U]=Y[K+U]*E+Y[H+U]*G;return W}}class x$ extends G7{constructor(J,$,Q,Z){super(J,$,Q,Z)}interpolate_(J){return this.copySampleValue_(J-1)}}class p0{constructor(J,$,Q,Z){if(J===void 0)throw Error("THREE.KeyframeTrack: track name is undefined");if($===void 0||$.length===0)throw Error("THREE.KeyframeTrack: no keyframes in track named "+J);this.name=J,this.times=u7($,this.TimeBufferType),this.values=u7(Q,this.ValueBufferType),this.setInterpolation(Z||this.DefaultInterpolation)}static toJSON(J){let $=J.constructor,Q;if($.toJSON!==this.toJSON)Q=$.toJSON(J);else{Q={name:J.name,times:u7(J.times,Array),values:u7(J.values,Array)};let Z=J.getInterpolation();if(Z!==J.DefaultInterpolation)Q.interpolation=Z}return Q.type=J.ValueTypeName,Q}InterpolantFactoryMethodDiscrete(J){return new x$(this.times,this.values,this.getValueSize(),J)}InterpolantFactoryMethodLinear(J){return new b$(this.times,this.values,this.getValueSize(),J)}InterpolantFactoryMethodSmooth(J){return new h$(this.times,this.values,this.getValueSize(),J)}setInterpolation(J){let $;switch(J){case 2300:$=this.InterpolantFactoryMethodDiscrete;break;case 2301:$=this.InterpolantFactoryMethodLinear;break;case 2302:$=this.InterpolantFactoryMethodSmooth;break}if($===void 0){let Q="unsupported interpolation for "+this.ValueTypeName+" keyframe track named "+this.name;if(this.createInterpolant===void 0)if(J!==this.DefaultInterpolation)this.setInterpolation(this.DefaultInterpolation);else throw Error(Q);return console.warn("THREE.KeyframeTrack:",Q),this}return this.createInterpolant=$,this}getInterpolation(){switch(this.createInterpolant){case this.InterpolantFactoryMethodDiscrete:return 2300;case this.InterpolantFactoryMethodLinear:return 2301;case this.InterpolantFactoryMethodSmooth:return 2302}}getValueSize(){return this.values.length/this.times.length}shift(J){if(J!==0){let $=this.times;for(let Q=0,Z=$.length;Q!==Z;++Q)$[Q]+=J}return this}scale(J){if(J!==1){let $=this.times;for(let Q=0,Z=$.length;Q!==Z;++Q)$[Q]*=J}return this}trim(J,$){let Q=this.times,Z=Q.length,W=0,Y=Z-1;while(W!==Z&&Q[W]<J)++W;while(Y!==-1&&Q[Y]>$)--Y;if(++Y,W!==0||Y!==Z){if(W>=Y)Y=Math.max(Y,1),W=Y-1;let X=this.getValueSize();this.times=Q.slice(W,Y),this.values=this.values.slice(W*X,Y*X)}return this}validate(){let J=!0,$=this.getValueSize();if($-Math.floor($)!==0)console.error("THREE.KeyframeTrack: Invalid value size in track.",this),J=!1;let Q=this.times,Z=this.values,W=Q.length;if(W===0)console.error("THREE.KeyframeTrack: Track is empty.",this),J=!1;let Y=null;for(let X=0;X!==W;X++){let H=Q[X];if(typeof H==="number"&&isNaN(H)){console.error("THREE.KeyframeTrack: Time is not a valid number.",this,X,H),J=!1;break}if(Y!==null&&Y>H){console.error("THREE.KeyframeTrack: Out of order keys.",this,X,H,Y),J=!1;break}Y=H}if(Z!==void 0){if(i4(Z))for(let X=0,H=Z.length;X!==H;++X){let K=Z[X];if(isNaN(K)){console.error("THREE.KeyframeTrack: Value is not a valid number.",this,X,K),J=!1;break}}}return J}optimize(){let J=this.times.slice(),$=this.values.slice(),Q=this.getValueSize(),Z=this.getInterpolation()===2302,W=J.length-1,Y=1;for(let X=1;X<W;++X){let H=!1,K=J[X],G=J[X+1];if(K!==G&&(X!==1||K!==J[0]))if(!Z){let E=X*Q,U=E-Q,q=E+Q;for(let D=0;D!==Q;++D){let N=$[E+D];if(N!==$[U+D]||N!==$[q+D]){H=!0;break}}}else H=!0;if(H){if(X!==Y){J[Y]=J[X];let E=X*Q,U=Y*Q;for(let q=0;q!==Q;++q)$[U+q]=$[E+q]}++Y}}if(W>0){J[Y]=J[W];for(let X=W*Q,H=Y*Q,K=0;K!==Q;++K)$[H+K]=$[X+K];++Y}if(Y!==J.length)this.times=J.slice(0,Y),this.values=$.slice(0,Y*Q);else this.times=J,this.values=$;return this}clone(){let J=this.times.slice(),$=this.values.slice(),Z=new this.constructor(this.name,J,$);return Z.createInterpolant=this.createInterpolant,Z}}p0.prototype.TimeBufferType=Float32Array;p0.prototype.ValueBufferType=Float32Array;p0.prototype.DefaultInterpolation=2301;class c6 extends p0{constructor(J,$,Q){super(J,$,Q)}}c6.prototype.ValueTypeName="bool";c6.prototype.ValueBufferType=Array;c6.prototype.DefaultInterpolation=2300;c6.prototype.InterpolantFactoryMethodLinear=void 0;c6.prototype.InterpolantFactoryMethodSmooth=void 0;class p$ extends p0{}p$.prototype.ValueTypeName="color";class g$ extends p0{}g$.prototype.ValueTypeName="number";class m$ extends G7{constructor(J,$,Q,Z){super(J,$,Q,Z)}interpolate_(J,$,Q,Z){let W=this.resultBuffer,Y=this.sampleValues,X=this.valueSize,H=(Q-$)/(Z-$),K=J*X;for(let G=K+X;K!==G;K+=4)M6.slerpFlat(W,0,Y,K-X,Y,K,H);return W}}class J9 extends p0{InterpolantFactoryMethodLinear(J){return new m$(this.times,this.values,this.getValueSize(),J)}}J9.prototype.ValueTypeName="quaternion";J9.prototype.InterpolantFactoryMethodSmooth=void 0;class n6 extends p0{constructor(J,$,Q){super(J,$,Q)}}n6.prototype.ValueTypeName="string";n6.prototype.ValueBufferType=Array;n6.prototype.DefaultInterpolation=2300;n6.prototype.InterpolantFactoryMethodLinear=void 0;n6.prototype.InterpolantFactoryMethodSmooth=void 0;class u$ extends p0{}u$.prototype.ValueTypeName="vector";class l${constructor(J,$,Q){let Z=this,W=!1,Y=0,X=0,H=void 0,K=[];this.onStart=void 0,this.onLoad=J,this.onProgress=$,this.onError=Q,this.itemStart=function(G){if(X++,W===!1){if(Z.onStart!==void 0)Z.onStart(G,Y,X)}W=!0},this.itemEnd=function(G){if(Y++,Z.onProgress!==void 0)Z.onProgress(G,Y,X);if(Y===X){if(W=!1,Z.onLoad!==void 0)Z.onLoad()}},this.itemError=function(G){if(Z.onError!==void 0)Z.onError(G)},this.resolveURL=function(G){if(H)return H(G);return G},this.setURLModifier=function(G){return H=G,this},this.addHandler=function(G,E){return K.push(G,E),this},this.removeHandler=function(G){let E=K.indexOf(G);if(E!==-1)K.splice(E,2);return this},this.getHandler=function(G){for(let E=0,U=K.length;E<U;E+=2){let q=K[E],D=K[E+1];if(q.global)q.lastIndex=0;if(q.test(G))return D}return null}}}var o4=new l$;class d${constructor(J){this.manager=J!==void 0?J:o4,this.crossOrigin="anonymous",this.withCredentials=!1,this.path="",this.resourcePath="",this.requestHeader={}}load(){}loadAsync(J,$){let Q=this;return new Promise(function(Z,W){Q.load(J,Z,$,W)})}parse(){}setCrossOrigin(J){return this.crossOrigin=J,this}setWithCredentials(J){return this.withCredentials=J,this}setPath(J){return this.path=J,this}setResourcePath(J){return this.resourcePath=J,this}setRequestHeader(J){return this.requestHeader=J,this}}d$.DEFAULT_MATERIAL_NAME="__DEFAULT";var $9="\\[\\]\\.:\\/",a4=new RegExp("["+$9+"]","g"),Q9="[^"+$9+"]",r4="[^"+$9.replace("\\.","")+"]",t4=/((?:WC+[\/:])*)/.source.replace("WC",Q9),e4=/(WCOD+)?/.source.replace("WCOD",r4),JY=/(?:\.(WC+)(?:\[(.+)\])?)?/.source.replace("WC",Q9),$Y=/\.(WC+)(?:\[(.+)\])?/.source.replace("WC",Q9),QY=new RegExp("^"+t4+e4+JY+$Y+"$"),ZY=["material","materials","bones","map"];class c${constructor(J,$,Q){let Z=Q||rJ.parseTrackName($);this._targetGroup=J,this._bindings=J.subscribe_($,Z)}getValue(J,$){this.bind();let Q=this._targetGroup.nCachedObjects_,Z=this._bindings[Q];if(Z!==void 0)Z.getValue(J,$)}setValue(J,$){let Q=this._bindings;for(let Z=this._targetGroup.nCachedObjects_,W=Q.length;Z!==W;++Z)Q[Z].setValue(J,$)}bind(){let J=this._bindings;for(let $=this._targetGroup.nCachedObjects_,Q=J.length;$!==Q;++$)J[$].bind()}unbind(){let J=this._bindings;for(let $=this._targetGroup.nCachedObjects_,Q=J.length;$!==Q;++$)J[$].unbind()}}class rJ{constructor(J,$,Q){this.path=$,this.parsedPath=Q||rJ.parseTrackName($),this.node=rJ.findNode(J,this.parsedPath.nodeName),this.rootNode=J,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}static create(J,$,Q){if(!(J&&J.isAnimationObjectGroup))return new rJ(J,$,Q);else return new rJ.Composite(J,$,Q)}static sanitizeNodeName(J){return J.replace(/\s/g,"_").replace(a4,"")}static parseTrackName(J){let $=QY.exec(J);if($===null)throw Error("PropertyBinding: Cannot parse trackName: "+J);let Q={nodeName:$[2],objectName:$[3],objectIndex:$[4],propertyName:$[5],propertyIndex:$[6]},Z=Q.nodeName&&Q.nodeName.lastIndexOf(".");if(Z!==void 0&&Z!==-1){let W=Q.nodeName.substring(Z+1);if(ZY.indexOf(W)!==-1)Q.nodeName=Q.nodeName.substring(0,Z),Q.objectName=W}if(Q.propertyName===null||Q.propertyName.length===0)throw Error("PropertyBinding: can not parse propertyName from trackName: "+J);return Q}static findNode(J,$){if($===void 0||$===""||$==="."||$===-1||$===J.name||$===J.uuid)return J;if(J.skeleton){let Q=J.skeleton.getBoneByName($);if(Q!==void 0)return Q}if(J.children){let Q=function(W){for(let Y=0;Y<W.length;Y++){let X=W[Y];if(X.name===$||X.uuid===$)return X;let H=Q(X.children);if(H)return H}return null},Z=Q(J.children);if(Z)return Z}return null}_getValue_unavailable(){}_setValue_unavailable(){}_getValue_direct(J,$){J[$]=this.targetObject[this.propertyName]}_getValue_array(J,$){let Q=this.resolvedProperty;for(let Z=0,W=Q.length;Z!==W;++Z)J[$++]=Q[Z]}_getValue_arrayElement(J,$){J[$]=this.resolvedProperty[this.propertyIndex]}_getValue_toArray(J,$){this.resolvedProperty.toArray(J,$)}_setValue_direct(J,$){this.targetObject[this.propertyName]=J[$]}_setValue_direct_setNeedsUpdate(J,$){this.targetObject[this.propertyName]=J[$],this.targetObject.needsUpdate=!0}_setValue_direct_setMatrixWorldNeedsUpdate(J,$){this.targetObject[this.propertyName]=J[$],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_array(J,$){let Q=this.resolvedProperty;for(let Z=0,W=Q.length;Z!==W;++Z)Q[Z]=J[$++]}_setValue_array_setNeedsUpdate(J,$){let Q=this.resolvedProperty;for(let Z=0,W=Q.length;Z!==W;++Z)Q[Z]=J[$++];this.targetObject.needsUpdate=!0}_setValue_array_setMatrixWorldNeedsUpdate(J,$){let Q=this.resolvedProperty;for(let Z=0,W=Q.length;Z!==W;++Z)Q[Z]=J[$++];this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_arrayElement(J,$){this.resolvedProperty[this.propertyIndex]=J[$]}_setValue_arrayElement_setNeedsUpdate(J,$){this.resolvedProperty[this.propertyIndex]=J[$],this.targetObject.needsUpdate=!0}_setValue_arrayElement_setMatrixWorldNeedsUpdate(J,$){this.resolvedProperty[this.propertyIndex]=J[$],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_fromArray(J,$){this.resolvedProperty.fromArray(J,$)}_setValue_fromArray_setNeedsUpdate(J,$){this.resolvedProperty.fromArray(J,$),this.targetObject.needsUpdate=!0}_setValue_fromArray_setMatrixWorldNeedsUpdate(J,$){this.resolvedProperty.fromArray(J,$),this.targetObject.matrixWorldNeedsUpdate=!0}_getValue_unbound(J,$){this.bind(),this.getValue(J,$)}_setValue_unbound(J,$){this.bind(),this.setValue(J,$)}bind(){let J=this.node,$=this.parsedPath,Q=$.objectName,Z=$.propertyName,W=$.propertyIndex;if(!J)J=rJ.findNode(this.rootNode,$.nodeName),this.node=J;if(this.getValue=this._getValue_unavailable,this.setValue=this._setValue_unavailable,!J){console.warn("THREE.PropertyBinding: No target node found for track: "+this.path+".");return}if(Q){let K=$.objectIndex;switch(Q){case"materials":if(!J.material){console.error("THREE.PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!J.material.materials){console.error("THREE.PropertyBinding: Can not bind to material.materials as node.material does not have a materials array.",this);return}J=J.material.materials;break;case"bones":if(!J.skeleton){console.error("THREE.PropertyBinding: Can not bind to bones as node does not have a skeleton.",this);return}J=J.skeleton.bones;for(let G=0;G<J.length;G++)if(J[G].name===K){K=G;break}break;case"map":if("map"in J){J=J.map;break}if(!J.material){console.error("THREE.PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!J.material.map){console.error("THREE.PropertyBinding: Can not bind to material.map as node.material does not have a map.",this);return}J=J.material.map;break;default:if(J[Q]===void 0){console.error("THREE.PropertyBinding: Can not bind to objectName of node undefined.",this);return}J=J[Q]}if(K!==void 0){if(J[K]===void 0){console.error("THREE.PropertyBinding: Trying to bind to objectIndex of objectName, but is undefined.",this,J);return}J=J[K]}}let Y=J[Z];if(Y===void 0){let K=$.nodeName;console.error("THREE.PropertyBinding: Trying to update property for track: "+K+"."+Z+" but it wasn't found.",J);return}let X=this.Versioning.None;if(this.targetObject=J,J.needsUpdate!==void 0)X=this.Versioning.NeedsUpdate;else if(J.matrixWorldNeedsUpdate!==void 0)X=this.Versioning.MatrixWorldNeedsUpdate;let H=this.BindingType.Direct;if(W!==void 0){if(Z==="morphTargetInfluences"){if(!J.geometry){console.error("THREE.PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.",this);return}if(!J.geometry.morphAttributes){console.error("THREE.PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.morphAttributes.",this);return}if(J.morphTargetDictionary[W]!==void 0)W=J.morphTargetDictionary[W]}H=this.BindingType.ArrayElement,this.resolvedProperty=Y,this.propertyIndex=W}else if(Y.fromArray!==void 0&&Y.toArray!==void 0)H=this.BindingType.HasFromToArray,this.resolvedProperty=Y;else if(Array.isArray(Y))H=this.BindingType.EntireArray,this.resolvedProperty=Y;else this.propertyName=Z;this.getValue=this.GetterByBindingType[H],this.setValue=this.SetterByBindingTypeAndVersioning[H][X]}unbind(){this.node=null,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}}rJ.Composite=c$;rJ.prototype.BindingType={Direct:0,EntireArray:1,ArrayElement:2,HasFromToArray:3};rJ.prototype.Versioning={None:0,NeedsUpdate:1,MatrixWorldNeedsUpdate:2};rJ.prototype.GetterByBindingType=[rJ.prototype._getValue_direct,rJ.prototype._getValue_array,rJ.prototype._getValue_arrayElement,rJ.prototype._getValue_toArray];rJ.prototype.SetterByBindingTypeAndVersioning=[[rJ.prototype._setValue_direct,rJ.prototype._setValue_direct_setNeedsUpdate,rJ.prototype._setValue_direct_setMatrixWorldNeedsUpdate],[rJ.prototype._setValue_array,rJ.prototype._setValue_array_setNeedsUpdate,rJ.prototype._setValue_array_setMatrixWorldNeedsUpdate],[rJ.prototype._setValue_arrayElement,rJ.prototype._setValue_arrayElement_setNeedsUpdate,rJ.prototype._setValue_arrayElement_setMatrixWorldNeedsUpdate],[rJ.prototype._setValue_fromArray,rJ.prototype._setValue_fromArray_setNeedsUpdate,rJ.prototype._setValue_fromArray_setMatrixWorldNeedsUpdate]];var XY=new Float32Array(1);if(typeof __THREE_DEVTOOLS__<"u")__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:"170"}}));if(typeof window<"u")if(window.__THREE__)console.warn("WARNING: Multiple instances of Three.js being imported.");else window.__THREE__="170";var n$=[200,300,350,400,500,600],YY=0.42;function HY(J,$,Q){let Z=J.attributes.position,W=J.index,Y=W?W.count/3:Z.count/3,X=new v,H=new v,K=new v,G=[],E=0,U=(q,D)=>D.fromBufferAttribute(Z,W?W.getX(q):q);for(let q=0;q<Y;q++)U(q*3,X),U(q*3+1,H),U(q*3+2,K),E+=H.clone().sub(X).cross(K.clone().sub(X)).length()/2,G.push(E);for(let q=0;q<$;q++){let D=Math.random()*E,N=0,O=G.length-1;while(N<O){let z=N+O>>1;if(G[z]<D)N=z+1;else O=z}U(N*3,X),U(N*3+1,H),U(N*3+2,K);let V=Math.random(),F=Math.random();if(V+F>1)V=1-V,F=1-F;let A=()=>(Math.random()-0.5)*0.02;Q.push(X.x+(H.x-X.x)*V+(K.x-X.x)*F+A(),X.y+(H.y-X.y)*V+(K.y-X.y)*F+A(),X.z+(H.z-X.z)*V+(K.z-X.z)*F+A())}}function KY(J){let $=new s8({canvas:J,antialias:!0,alpha:!0});$.setPixelRatio(Math.min(2,devicePixelRatio||1));let Q=new i8,Z=new k0(32,1.6,0.1,100);Z.position.set(4.75,3.1,5.1),Z.lookAt(0,0.7,0);let W=new s0;Q.add(W);let Y=[],X=(d=1)=>new H7({color:789516,transparent:!0,opacity:d,polygonOffset:!0,polygonOffsetFactor:1,polygonOffsetUnits:1}),H=(d=1)=>new X7({color:16777215,transparent:!0,opacity:d});function K(d,KJ,WJ=600,{edge:AJ=0.85,threshold:pJ=20,dashed:C=!1,parent:lJ=W}={}){let CJ=new s0,mJ=new T0(d,X()),GJ=new e7(new t8(d,pJ),C?new e8({color:16777215,transparent:!0,dashSize:0.08,gapSize:0.06}):H());if(C)GJ.computeLineDistances();CJ.add(mJ,GJ),lJ.add(CJ);let $0={obj:CJ,min:KJ,max:WJ,edge:AJ,mats:[mJ.material,GJ.material],a:0,mesh:mJ};return Y.push($0),CJ}function G(d,KJ,WJ=600,AJ=0.7){let pJ=new V0().setFromPoints(d),C=new e7(pJ,H());W.add(C);let lJ={obj:C,min:KJ,max:WJ,edge:AJ,mats:[C.material],a:0,lineOnly:!0};return Y.push(lJ),C}function E(d,KJ,WJ,AJ=600,pJ=0.42){let lJ=document.createElement("canvas"),CJ=lJ.getContext("2d");CJ.font="500 30px ui-monospace, SFMono-Regular, Menlo, monospace",lJ.width=Math.max(256,Math.ceil(CJ.measureText(d).width)+24),lJ.height=64,CJ.font="500 30px ui-monospace, SFMono-Regular, Menlo, monospace",CJ.fillStyle="#fff",CJ.textAlign="center",CJ.textBaseline="middle",CJ.fillText(d,lJ.width/2,32);let mJ=new r8(lJ);mJ.colorSpace=K$;let GJ=new o8(new t7({map:mJ,transparent:!0,depthTest:!1}));return GJ.scale.set(pJ*4*(lJ.width/256),pJ,1),GJ.position.copy(KJ),GJ.renderOrder=10,W.add(GJ),Y.push({obj:GJ,min:WJ,max:AJ,edge:0.9,mats:[GJ.material],a:0,lineOnly:!0}),GJ}let U=(d,KJ,WJ=28)=>new $8(d,d,KJ,WJ),q=(d,KJ,WJ)=>new v(d,KJ,WJ);K(new X0(2.6,0.12,1.1),200,200).position.set(0,0.06,0),K(new X0(1.9,0.75,0.75),200,200).position.set(-0.25,0.5,0),K(new X0(0.3,1.2,0.3),200,200).position.set(0.95,0.95,0),K(new X0(0.3,0.3,1.5),200,200).position.set(0.95,1.55,-0.6),K(new X0(0.42,0.42,0.42),200,200).position.set(0.95,1.55,-0.95),E("≈ ±150 mm",q(-0.25,1.15,0.5),200,200),K(new X0(2.6,0.08,1),300).position.set(0,0.04,0);for(let d of[-1.2,1.2])K(new X0(0.08,0.14,1),300).position.set(d,0.07,0);let N=K(U(0.3,1,36),300,600,{threshold:30});N.rotation.z=Math.PI/2,N.position.set(-0.6,0.48,0);for(let d=0;d<6;d++){let KJ=K(U(0.325,0.03,36),300,600,{edge:0.4});KJ.rotation.z=Math.PI/2,KJ.position.set(-0.98+d*0.13,0.48,0)}let O=K(new K7(0.29,24,12,0,Math.PI*2,0,Math.PI/2),300,600,{threshold:40});O.rotation.z=Math.PI/2,O.position.set(-1.1,0.48,0),K(new X0(0.7,0.18,0.62),300).position.set(-0.6,0.17,0);let V=K(U(0.12,0.22),300);V.rotation.z=Math.PI/2,V.position.set(0,0.48,0);let F=K(U(0.38,0.32,40),300,600,{threshold:30});F.rotation.z=Math.PI/2,F.position.set(0.45,0.55,0),K(new X0(0.42,0.22,0.5),300).position.set(0.42,0.19,0);let A=K(U(0.11,0.55),300);A.rotation.z=Math.PI/2,A.position.set(0.88,0.55,0),K(U(0.1,0.9),300).position.set(0.45,1.25,0);let z=K(new B6(0.2,0.1,14,24,Math.PI/2),300,600,{threshold:35});z.rotation.y=Math.PI/2,z.position.set(0.45,1.7,-0.2);let _=K(U(0.1,1.1),300);_.rotation.x=Math.PI/2,_.position.set(0.45,1.9,-0.75),K(new K7(0.19,22,14),300,600,{threshold:40}).position.set(0.45,1.9,-0.75),K(U(0.025,0.4),300).position.set(0.45,2.15,-0.75);let L=K(new B6(0.16,0.022,8,28),300,600,{threshold:40});L.rotation.x=Math.PI/2,L.position.set(0.45,2.36,-0.75);for(let d of[0,Math.PI/2]){let KJ=K(new X0(0.3,0.018,0.018),300,600,{edge:0.6,parent:L});KJ.rotation.z=d}let P=(d,KJ,WJ,AJ,pJ,C=300)=>{let lJ=new v().subVectors(KJ,d).normalize(),CJ=WJ.clone().normalize().multiplyScalar(0.08);return G([d.clone().add(WJ),KJ.clone().add(WJ),d.clone().add(WJ).sub(CJ),d.clone().add(WJ).add(CJ),KJ.clone().add(WJ).sub(CJ),KJ.clone().add(WJ).add(CJ),d,d.clone().add(WJ),KJ,KJ.clone().add(WJ)],C,600,0.55),E(AJ,pJ,C,600,0.36),lJ};P(q(-1.3,0,0.55),q(1.3,0,0.55),q(0,0,0.35),"2 600",q(0,0.12,1.05)),P(q(1.3,0,-0.5),q(1.3,1.9,-0.5),q(0.35,0,0),"1 900",q(1.95,0.95,-0.5));let p=(d,KJ,WJ,AJ=350)=>{let pJ=K(U(0.18,0.05,32),AJ,500,{threshold:30});return pJ.position.copy(d),pJ.rotation.x=KJ,pJ.rotation.z=WJ,pJ},B=[p(q(0.45,0.83,0),0,0),p(q(1.14,0.55,0),0,Math.PI/2),p(q(0.45,1.9,-0.52),Math.PI/2,0),p(q(0.45,1.9,-0.98),Math.PI/2,0)];K(new X0(0.08,1.8,0.08),350).position.set(0.45,0.98,-1.15),K(new B6(0.12,0.02,6,20,Math.PI),350,600,{threshold:40}).position.set(0.45,1.9,-1.15),K(new X0(0.4,0.04,0.4),350).position.set(0.45,0.02,-1.15);for(let d of[-1.15,1.15])for(let KJ of[-0.42,0.42])K(U(0.025,0.22,10),350,600,{edge:0.6}).position.set(d,0.12,KJ);let T=K(new X0(0.9,1,0.9),350,600,{dashed:!0,edge:0.55});T.position.set(-1.8,0.5,0),T.children[0].material.opacity=0,T.children[0].visible=!1,E("access zone",q(-1.8,1.2,0),350,500,0.36);let x=[];B.forEach((d)=>{let KJ=new s0;d.add(KJ),x.push({g:KJ,f:d,home:d.position.clone()});for(let WJ=0;WJ<8;WJ++){let AJ=WJ/8*Math.PI*2;K(U(0.016,0.12,8),400,600,{edge:0.7,parent:KJ}).position.set(Math.cos(AJ)*0.14,0,Math.sin(AJ)*0.14)}});for(let[d,KJ]of[[q(0.45,1.52,0),0],[q(0.45,1.9,-0.2),Math.PI/2],[q(0.45,0.88,0),0]]){let WJ=K(new B6(0.105,0.012,6,24),400,600,{edge:0.8,threshold:60});WJ.position.copy(d),WJ.rotation.x=Math.PI/2+KJ}K(new X0(0.22,0.12,0.01),400).position.set(-0.6,0.62,0.31),E("P-101",q(0.45,1.05,0.55),400,500),E("DN100 PN16",q(0.45,2.15,-1.45),400,500,0.32);let m=[];W.updateMatrixWorld(!0),Y.filter((d)=>d.mesh&&d.min>=300&&d.min<=350&&d.obj.parent===W&&d.obj!==T).forEach((d)=>{let KJ=d.mesh.geometry.clone().applyMatrix4(d.obj.matrixWorld);KJ.computeBoundingBox();let WJ=KJ.boundingBox.getSize(new v);HY(KJ,Math.round(Math.min(1600,120+(WJ.x*WJ.y+WJ.y*WJ.z+WJ.x*WJ.z)*900)),m)});let u=new V0;u.setAttribute("position",new Y0(m,3));let a={value:-2},l=new J8({color:16777215,size:0.022,transparent:!0,opacity:0,depthWrite:!1});l.onBeforeCompile=(d)=>{d.uniforms.uSweep=a,d.vertexShader=`uniform float uSweep; varying float vX;
`+d.vertexShader.replace("#include <begin_vertex>",`#include <begin_vertex>
vX = position.x;`),d.fragmentShader=`uniform float uSweep; varying float vX;
`+d.fragmentShader.replace("#include <clipping_planes_fragment>",`if (vX > uSweep) discard;
#include <clipping_planes_fragment>`)};let t=new a8(u,l);W.add(t),Y.push({obj:t,min:500,max:500,edge:0.75,mats:[l],a:0,lineOnly:!0});let g=G([q(0,-0.05,-1.4),q(0,2.6,-1.4),q(0,2.6,-1.4),q(0,2.6,0.7),q(0,2.6,0.7),q(0,-0.05,0.7),q(0,-0.05,0.7),q(0,-0.05,-1.4)],500,500,0.9);E("✓ 4 mm",q(-1.25,0.95,0.35),500,500,0.34),E("✓ 6 mm",q(0.45,2.55,-0.4),500,500,0.34),E("✓ 3 mm",q(1.4,0.55,0.4),500,500,0.34);let XJ=(d,KJ,WJ,AJ,pJ,C)=>K(new X0(d,KJ,WJ),600,600,{dashed:!0,edge:0.75}).position.set(AJ,pJ,C);XJ(1.25,0.72,0.72,-0.6,0.48,0),XJ(0.52,0.86,0.86,0.45,0.5,0),XJ(2.62,0.16,1.04,0,0.08,0),XJ(0.46,0.46,0.46,0.45,1.9,-0.75),E("412 kg",q(-1.15,0.95,0.45),600,600,0.34),E("μ 0.6 steel",q(1.55,0.25,0.6),600,600,0.3),E("joint · valve wheel",q(1.3,2.05,-0.75),600,600,0.3),E("collision shell",q(1.05,1.05,0.45),600,600,0.3);let ZJ=300,_J=0,fJ=!1,n=performance.now(),e=n;function zJ(d){if(n$.includes(d)&&d!==ZJ)ZJ=d,e=performance.now()}function kJ(){let{clientWidth:d,clientHeight:KJ}=J;if(!d||!KJ)return;$.setSize(d,KJ,!1),Z.aspect=d/KJ,Z.updateProjectionMatrix()}function YJ(d){_J=requestAnimationFrame(YJ);let KJ=(d-n)/1000,WJ=(d-e)/1000;W.rotation.y=-0.35+Math.sin(KJ*0.35)*0.45;for(let C of Y){let lJ=ZJ>=C.min&&ZJ<=C.max?C.min>=ZJ||ZJ===n$[0]||ZJ===300&&C.min<=300?1:YY:0;if(C.a+=(lJ-C.a)*0.12,C.obj.visible=C.a>0.01,C.lineOnly)C.mats[0].opacity=C.a*C.edge;else C.mats[0].opacity=C.a,C.mats[1].opacity=C.a*C.edge}T.children[1].material.opacity*=0.55+0.45*Math.sin(KJ*2.4);let AJ=ZJ===400?Math.max(0,Math.sin(WJ*1.4))*0.08:0;if(x.forEach(({f:C,home:lJ})=>{let CJ=new v(0,1,0).applyEuler(C.rotation);C.position.copy(lJ).addScaledVector(CJ,AJ)}),ZJ===600)L.rotation.z+=0.025;let pJ=-1.8+WJ*0.9%4.2;a.value=ZJ===500?Math.min(1.9,pJ):-2,g.position.x=Math.min(1.9,pJ),g.visible=ZJ===500&&pJ<1.9,$.render(Q,Z)}return{setLevel:zJ,start(){if(fJ)return;fJ=!0,kJ(),_J=requestAnimationFrame(YJ)},stop(){fJ=!1,cancelAnimationFrame(_J)},resize:kJ}}export{KY as createLodDemo};
